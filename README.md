# MouseLatch — Persistent Mouse Control for AI Agents

**One press. Multiple observations. Explicit release.**

MouseLatch restores a native input capability that many AI computer-use harnesses accidentally hide: mouse button state and cursor movement are **independent**. A finished `move()`, screenshot, tool call, or agent reasoning turn should not implicitly emit `mouseup`.

**中文摘要：** MouseLatch 将按键状态与光标运动彻底解耦，让 Agent 在多个独立决策轮次间持续按住鼠标，并在最后显式释放。适用于复杂拖拽、时间轴剪辑、画图、视觉反馈控制与滑块交互。

## Why it matters

A high-level `drag(start,end)` often bundles down → move → up. That is convenient for simple tasks, but it prevents a controller from holding the button through several rounds of observation and correction. MouseLatch makes `press`, `move`, `observe`, and `release` independent primitives backed by a **persistent browser worker**.

```python
mouse.press("left")
mouse.move(x1, y1)
frame1 = mouse.observe()
# The agent can think and make a new RPC while the mouse remains held.
mouse.move(x2, y2)
frame2 = mouse.observe()
mouse.release("left")
```

The snippet illustrates the intended API; the current code includes a reference transition model and a live browser test worker rather than a packaged production API.

## Formal specification

- [State model and invariants](docs/FORMAL_MODEL.md) — mathematical contract, button-state orthogonality and explicit emergency abort.
- [Scientific validation protocol](docs/VALIDATION_PROTOCOL.md) — falsification criteria, paired benchmark design, outside-webpage testing.
- [Real public site integration tests](tests/live_public_demos.py) — separate localhost HTTP calls controlling one persistent Chromium browser against official jQuery UI **slider / draggable / droppable** demo pages.
- [GitHub Actions runner](.github/workflows/live-browser-tests.yml) — automatically captures browser event counts, JSON reports and screenshots.

## Run tests

```bash
python3 -m unittest discover -s tests -p test_formal_model.py -v
pip install -r requirements.txt
# Linux: install chromium (for example: sudo apt install chromium)
python3 tests/live_public_demos.py
```

The actual public-site test needs Chromium at `/usr/bin/chromium` and access to `jqueryui.com`. CI stores evidence in an Actions artifact. A network error is not a proof of interface failure.

## Demo and scientific evidence

A previous **first-party synthetic slider** exploratory experiment with randomized gain and target position reported **40/40** visual closed-loop success versus **2/40** one-shot, both using the same random seeds. These are initial development measurements, not an independent hold-out validation or real CAPTCHA pass rate. See the validation protocol for the planned repeatable benchmark.

The new real-website suite tests public UI controls and counts actual DOM mousedown/mouseup events rather than trusting only a Python Boolean. This is not a system for bypassing third-party site security checks. Some protected pages need authorized APIs, account verification, or human assistance.

## Philosophy

**Do not create artificial restrictions on an agent's accessible physical input primitives.** Keep convenience `click()` and `drag()` methods if useful, but never make them the only available level of control. Stateful inputs should be explicit, observable, composable and recoverable after exceptions.

## License

MIT. Contributions, reproductions, and issue reports welcome.
