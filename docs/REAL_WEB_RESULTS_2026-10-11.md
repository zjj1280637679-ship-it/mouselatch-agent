# First verified public-website integration run

**Date:** 2026-10-11 UTC (initial GitHub Actions run)

**Run:** https://github.com/zjj1280637679-ship-it/mouselatch-agent/actions/runs/38109947187

**Environment:** GitHub-hosted Linux runner, headless Chromium, Playwright Python, local HTTP RPC service using one persistent browser context.

## Results

| Official public demo | Independent moves | Held states during both observations | Browser down/up | Final outcome |
|---|---:|---|---:|---|
| [jQuery UI Slider](https://jqueryui.com/resources/demos/slider/default.html) | 2 | true / true | 1 / 1 | PASS |
| [jQuery UI Draggable](https://jqueryui.com/resources/demos/draggable/default.html) | 2 | true / true | 1 / 1 | PASS |
| [jQuery UI Droppable](https://jqueryui.com/resources/demos/droppable/default.html) | 2 | true / true | 1 / 1 | PASS, `Dropped!` |

The initial observations were taken before mouse down; subsequent observations show `[false, true, true, false]` for held-state before/down/drag/after-release.

Data read from the downloaded CI JSON:

| Test | X coordinates of target DOM element in four successive observations (px) | Mouse event counts at completion |
|---|---|---|
| Slider | -0.6 → 34.9 → 105.8 → 105.8 | down=1, up=1, move=25 |
| Draggable | 8 → 46 → 118 → 118 | down=1, up=1, move=25 |
| Droppable | 8 → 46 → 171 → 171 | down=1, up=1, move=25 |

The worker snapshots are saved in the downloadable workflow artifact `mouselatch-real-site-test-evidence`. In each test, four PNGs and a `results.json` report were captured.

**What this establishes:** the underlying Chromium button state remains held across separate network calls to a persistent worker, during screenshot capture and further mouse movement. These results extend the state-transition principle to actual independently hosted UI libraries and handlers.

**What this does not establish:** resistance to CAPTCHA/anti-bot defenses, human-like motion, accessibility on social sites, or success under an arbitrary untested browser environment. The test obtains bounding boxes from the public UI's DOM as a measurement oracle; no claim is made here about black-box visual localization.

## The next falsification tests

1. Repeat across multiple viewport dimensions and device pixel ratios.
2. Insert 5–20 second asynchronous controller delays and verify no implicit release (up to the configured watchdog expiry).
3. Inject concurrent writers, timeouts, and browser-worker crashes, then inspect cleanup behavior.
4. Test more independently designed UI controls and pointer-event libraries.
5. Replicate the randomized first-party visual-feedback study with new unselected random seeds and confidence intervals.
