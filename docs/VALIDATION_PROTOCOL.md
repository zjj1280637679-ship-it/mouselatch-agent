# Scientific validation protocol

## P0 — state-machine properties

Run `python -m unittest discover -s tests -p test_formal_model.py -v`.

Assert invariants I1-I7 where applicable; verify that held state survives twenty separate move-observe-turn cycles; reject illegal duplicate presses; abort releases safely.

## P1 — randomized first-party visual slider

Randomize slider target distance, unknown mouse-to-object gain, nonlinear jitter and tolerance. Compare **paired seeds** for (A) open-loop one-shot control and (B) persistent held-state, screenshot-feedback control. Log trial seed, command trace, actual browser events, displacement, final error and outcome. Keep hidden ground truth inaccessible to the controller until release.

Previous exploratory first-party report: 40/40 with closed-loop versus 2/40 open-loop; the stress sample was tuned then rerun. These are **development measurements, not a new hold-out dataset**. Report binomial Wilson intervals and use fresh seeds for a proper new evaluation.

## P2 — real public web UI pages (not CAPTCHA)

Live targets:

- [jQuery UI Slider](https://jqueryui.com/resources/demos/slider/default.html) — `#slider .ui-slider-handle`.
- [jQuery UI Draggable](https://jqueryui.com/resources/demos/draggable/default.html) — `#draggable`.
- [jQuery UI Droppable](https://jqueryui.com/resources/demos/droppable/default.html) — `#draggable` moved to `#droppable`.

Each target receives 1 real browser mousedown, **multiple independent HTTP move+observe operations**, and 1 explicit mouseup. Assert no premature mouseup, browser-side event counts, visible position change, and the final drop effect.

The test framework may inspect DOM bounding boxes **as independent instrumentation**. These public UI demos are transfer tests of input-state semantics, not black-box CAPTCHA solver benchmarks. Record site availability separately from controller failure.

## P3 — failure injection and operational safety

Test agent latency, watchdog expiration, worker crashes, session changes, simultaneous clients, browser resize/zoom and unsupported pointer targets. Log whether cleanup was deliberate or exceptional. Never conflate “test not run” with “test passed”.

## Reporting format

Collect attempted / passed / failed / environment-blocked / skipped, Chromium version, site URL, command timestamps, screenshots, input events, and error text. Success on a benign widget does not demonstrate evasion of real website access controls. For protected services, use normal authorization or user-assisted verification.
