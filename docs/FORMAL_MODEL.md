# Formal Model: MouseLatch input-state orthogonality

## The claim

MouseLatch removes an unnecessary *tool API restriction*: finishing a pointer movement, screenshot, or AI decision turn must not implicitly change the mouse button state. It restores an already-available OS/browser behavior to cross-call agent interfaces; it does **not** invent a new physical mouse capability.

Let the execution state be **S = (B, P, C, L, H)**, with:

- **B** = set of held buttons (left/right/middle).
- **P** = cursor coordinate (x, y), in CSS pixels.
- **C** = persistent browser context.
- **L** = exclusive owner and serialized input-command queue.
- **H** = heartbeat, lease deadline, and recovery status.

Initial state: **B = empty**, active context **C**.

## Commands and transition function

| Command | Precondition | Button-state transition |
|---|---|---|
| press(b) | b not in B | B' = B union {b} |
| move(x,y) | C active | **B' = B** |
| observe() | C active | **B' = B** |
| agentTurnEnd() | C active | **B' = B** |
| release(b) | b in B | B' = B minus {b} |
| abort() | any | B' = empty (emergency) |

Other state: `move` changes P, `observe` reads a screenshot, `agentTurnEnd` ends a reasoning cycle; none is allowed to silently synthesize `mouseup`.

## Invariants

- **I1 Movement orthogonality:** G(move => B_after = B_before).
- **I2 Observation orthogonality:** G(observe => B_after = B_before).
- **I3 Turn orthogonality:** G(agentTurnEnd => B_after = B_before).
- **I4 Deliberate release:** in normal operation, only release(button) shrinks B; abort is an explicitly logged emergency exception.
- **I5 Valid transitions:** reject press of an already held button and release of an unheld button.
- **I6 Single hold event accounting:** one ordinary hold interaction has exactly one mousedown and one mouseup even when it contains N independent move/observe RPCs.
- **I7 No session leakage:** a newly owned session begins with B empty.

G means “always” in linear temporal logic. Input commands are serialized, tied to one persistent browser, and protected against conflicting owners.

## Eventual recovery

Assuming an abort mechanism or an operational watchdog exists, G(B != empty => F(B = empty)): held buttons eventually release after completion or an *exceptional* recovery. This **does not** mean an automatic mouseup after each move or snapshot. F means “eventually”.

## Three separate hypotheses

1. **H-architecture:** real browser mousedown/up events preserve state across independent RPC / agent-call boundaries.
2. **H-control:** while-held observation and correction improve accuracy against one-shot dragging on blinded first-party randomized targets.
3. **H-transfer:** the same mechanism works on independent third-party, public, non-security UI widgets.

Proof of an internal Boolean state is not a proof of real browser events. Proof of a first-party slider demonstration is not a measure of success against third-party CAPTCHA, which involves unrelated risk and abuse defenses.

## How the claim could fail

The architectural claim is falsified by unexpected mouseup on observe/move/turn boundary, inability to persist across independent RPCs, conflicting commands corrupting input state, or failure to release on explicit command/abort. Tests must capture browser-level event counters and screenshots to distinguish actual events from bookkeeping.
