#!/usr/bin/env python3
"""Integration test: true browser mouse hold across separate localhost HTTP RPCs.
Only visits public, non-security jQuery UI official demo pages.
"""
import asyncio
import json
from pathlib import Path
import sys
from aiohttp import ClientSession, ClientTimeout, web
from playwright.async_api import async_playwright

DEMOS = {
    "slider": ("https://jqueryui.com/resources/demos/slider/default.html", "#slider .ui-slider-handle"),
    "draggable": ("https://jqueryui.com/resources/demos/draggable/default.html", "#draggable"),
    "droppable": ("https://jqueryui.com/resources/demos/droppable/default.html", "#draggable"),
}
OUT = Path("results/live")
OUT.mkdir(parents=True, exist_ok=True)

class Worker:
    def __init__(self):
        self.pw = self.browser = self.page = None
        self.held = False
        self.site = None
        self.sequence = 0
        self.lock = asyncio.Lock()

    async def start(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(
            executable_path="/usr/bin/chromium", headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await self.browser.new_context(viewport={"width":1200,"height":780})
        await context.add_init_script("""
          window.__mlEventCount = {down: 0, up: 0, move: 0};
          document.addEventListener('mousedown', () => window.__mlEventCount.down++, true);
          document.addEventListener('mouseup', () => window.__mlEventCount.up++, true);
          document.addEventListener('mousemove', () => window.__mlEventCount.move++, true);
        """)
        self.page = await context.new_page()

    async def stop(self):
        if self.held:
            try: await self.page.mouse.up(button="left")
            finally: self.held = False
        if self.browser: await self.browser.close()
        if self.pw: await self.pw.stop()

    async def navigate(self, req):
        name = (await req.json()).get("site")
        if name not in DEMOS:
            return web.json_response({"error":"unapproved_demo"},status=400)
        async with self.lock:
            if self.held:
                return web.json_response({"error":"release_before_navigation"},status=409)
            self.site = name
            self.sequence = 0
            url, selector = DEMOS[name]
            response = await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
            if response is None or response.status >= 400:
                raise RuntimeError(f"Navigation failed: {url}: {response.status if response else 'null'}")
            await self.page.locator(selector).wait_for(timeout=20000)
            return web.json_response({"ok":True,"url":self.page.url,"http_status":response.status})

    async def down(self, req):
        data = await req.json()
        async with self.lock:
            if self.held:
                return web.json_response({"error":"already_held"},status=409)
            await self.page.mouse.move(float(data["x"]),float(data["y"]))
            await self.page.mouse.down(button="left")
            self.held = True
            return web.json_response({"ok":True,"held":True})

    async def move(self, req):
        data = await req.json()
        async with self.lock:
            if not self.held:
                return web.json_response({"error":"mouse_not_held"},status=409)
            await self.page.mouse.move(float(data["x"]),float(data["y"]),steps=12)
            return web.json_response({"ok":True,"held":True})

    async def up(self, req):
        async with self.lock:
            if not self.held:
                return web.json_response({"error":"mouse_not_held"},status=409)
            await self.page.mouse.up(button="left")
            self.held = False
            return web.json_response({"ok":True,"held":False})

    async def observe(self, req):
        async with self.lock:
            if not self.site: return web.json_response({"error":"no_session"},status=409)
            sel = DEMOS[self.site][1]
            rect = await self.page.locator(sel).bounding_box()
            target = await self.page.locator("#droppable").bounding_box() if self.site=="droppable" else None
            txt = await self.page.locator("#droppable").inner_text() if self.site=="droppable" else None
            events = await self.page.evaluate("window.__mlEventCount || null")
            state = {"held":self.held,"rect":rect,"target_rect":target,
                     "drop_text":txt,"browser_events":events,"url":self.page.url}
            self.sequence += 1
            await self.page.screenshot(path=str(OUT/f"{self.site}_{self.sequence:02}.png"))
            return web.json_response(state)

async def rpc(sess, method, url, **params):
    async with sess.request(method,url,**params) as r:
        payload = await r.json()
        if r.status >= 400: raise RuntimeError(f"RPC HTTP {r.status}: {payload}")
        return payload

def center(r):
    return (r["x"]+r["width"]/2,r["y"]+r["height"]/2)

def check(ok, reason):
    if not ok: raise AssertionError(reason)

async def scenario(name, root, sess):
    await rpc(sess,"POST",root+"/nav",json={"site":name})
    init = await rpc(sess,"GET",root+"/observe")
    sx,sy = center(init["rect"])
    await rpc(sess,"POST",root+"/down",json={"x":sx,"y":sy})
    await rpc(sess,"POST",root+"/move",json={"x":sx+38,"y":sy})
    a = await rpc(sess,"GET",root+"/observe")
    if name == "droppable":
        x,y=center(init["target_rect"])
        await rpc(sess,"POST",root+"/move",json={"x":x,"y":y})
    else:
        await rpc(sess,"POST",root+"/move",json={"x":sx+110,"y":sy})
    b = await rpc(sess,"GET",root+"/observe")
    check(a["held"] and b["held"],"held state lost during separate requests")
    check(a["browser_events"]["up"]==0 and b["browser_events"]["up"]==0,
          "unexpected real DOM mouseup before explicit release")
    check(b["browser_events"]["down"]==1,"browser did not receive exactly 1 mouse down")
    if name in ("slider","draggable"):
        xs=[z["rect"]["x"] for z in (init,a,b)]
        check(xs[1]>xs[0]+5 and xs[2]>xs[1]+10,f"no progressive movement: {xs}")
    await rpc(sess,"POST",root+"/up",json={})
    last = await rpc(sess,"GET",root+"/observe")
    check(not last["held"],"explicit mouse release failed")
    check(last["browser_events"]["down"]==1 and last["browser_events"]["up"]==1,
          f"browser event mismatch: {last['browser_events']}")
    if name=="droppable":
        check("Dropped!" in (last["drop_text"] or ""),f"drop rejected: {last['drop_text']}")
    return {"status":"passed","events":last["browser_events"],"observations":[init,a,b,last]}

async def main():
    worker=Worker()
    await worker.start()
    app=web.Application()
    app.add_routes([web.post("/nav",worker.navigate),web.post("/down",worker.down),
                    web.post("/move",worker.move),web.post("/up",worker.up),
                    web.get("/observe",worker.observe)])
    runner=web.AppRunner(app)
    await runner.setup()
    site=web.TCPSite(runner,"127.0.0.1",0)
    await site.start()
    port=site._server.sockets[0].getsockname()[1]
    root=f"http://127.0.0.1:{port}"
    report={}
    try:
        async with ClientSession(timeout=ClientTimeout(total=120)) as sess:
            for name in DEMOS:
                try:
                    report[name]=await scenario(name,root,sess)
                    print("PASS",name,flush=True)
                except Exception as exc:
                    report[name]={"status":"failed","error":str(exc)}
                    print("FAIL",name,repr(exc),flush=True)
                    if worker.held:
                        try: await rpc(sess,"POST",root+"/up",json={})
                        except Exception: pass
    finally:
        (OUT/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
        await runner.cleanup()
        await worker.stop()
    print("SUMMARY",json.dumps({k:v["status"] for k,v in report.items()}),flush=True)
    if any(x["status"]!="passed" for x in report.values()):
        sys.exit(1)

if __name__=="__main__":
    asyncio.run(main())
