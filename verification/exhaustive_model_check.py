#!/usr/bin/env python3
"""Exhaustive bounded state exploration: 2 buttons x 3 positions x 2 turns.
This checks the reference transition contract, not browser implementation.
"""
from collections import deque
from dataclasses import dataclass

BUTTONS=frozenset(("left","right"))
POSITIONS=(0,1,2)

@dataclass(frozen=True)
class State:
    held:frozenset[str]
    pos:int
    turn:int

def next_steps(s):
    for b in BUTTONS-s.held:
        yield ("press",b),State(s.held|{b},s.pos,s.turn)
    for b in s.held:
        yield ("release",b),State(s.held-{b},s.pos,s.turn)
    for p in POSITIONS:
        yield ("move",p),State(s.held,p,s.turn)
    yield ("observe",None),s
    yield ("turn_end",None),State(s.held,s.pos,1-s.turn)
    yield ("abort",None),State(frozenset(),s.pos,s.turn)

def verify():
    initial=State(frozenset(),0,0)
    visited={initial}
    pending=deque([initial])
    edges=0
    kinds={}
    violations=[]
    while pending:
        s=pending.popleft()
        assert s.held<=BUTTONS and s.pos in POSITIONS and s.turn in (0,1)
        for (op,arg),t in next_steps(s):
            edges+=1
            kinds[op]=kinds.get(op,0)+1
            if op in ("move","observe","turn_end") and t.held!=s.held:
                violations.append((s,op,"unexpected implicit release"))
            if op=="move" and (t.pos!=arg or t.turn!=s.turn):
                violations.append((s,op,"bad move"))
            if op=="observe" and t!=s:
                violations.append((s,op,"observe is not pure"))
            if op=="press" and (arg in s.held or t.held!=s.held|{arg}):
                violations.append((s,op,"bad press"))
            if op=="release" and (arg not in s.held or t.held!=s.held-{arg}):
                violations.append((s,op,"bad release"))
            if op=="abort" and t.held:
                violations.append((s,op,"abort failed to release"))
            if t not in visited:
                visited.add(t)
                pending.append(t)
    assert not violations, violations
    assert len(visited)==(2**len(BUTTONS))*len(POSITIONS)*2
    return {"status":"passed","states":len(visited),"transitions":edges,
            "commands":kinds,"buttons":sorted(BUTTONS),
            "positions":list(POSITIONS),"turns":2}

if __name__=="__main__":
    import json
    print(json.dumps(verify(),indent=2))
