# Duraknot Production Intelligence Dashboard

IoT-enabled production monitoring for the Duraknot fence-roll line — A-1 Launchpad 2026, Automation & Robotics Case Study 2. Team Forest.AI (Ayush Jha, Kavya Raval), MPSTME, NMIMS University.

**Live dashboard:** https://duraknotdashboard.vercel.app

**Status:** working dashboard running on a built-in simulator. The backend and ESP32 firmware are written and the backend's OEE calculation is unit-tested, but neither has been run against live sensors (see [`DATA_SOURCES.md`](DATA_SOURCES.md): no hardware was streaming data when this was written). OEE unit tests and a headless render check run in CI.

## Overview

The dashboard turns a fence-roll production line's raw signals (length produced, line speed, vibration-detected defects, running or stopped) into the numbers a production team manages by: **Overall Equipment Effectiveness (OEE = availability × performance × quality)**, defect patterns, alerts and shift-by-shift comparison. Views: live overview, OEE trend and loss breakdown, a defect Pareto and category breakdown, a full alert log, and a shift log.

Because no real sensor stream was available, the simulator's constants were checked against published industry benchmarks, and that paper trail is in [`DATA_SOURCES.md`](DATA_SOURCES.md).

## What's here

| Path | What it is |
|---|---|
| [`index.html`](index.html) | The dashboard itself. Single file, zero dependencies, runs offline. Ships with a built-in simulator so it's always demonstrable, and auto-detects a live backend if one is reachable (see the ⚙ Settings panel). |
| [`backend/`](backend/) | Flask REST API + SQLite persistence + alert engine that turns the dashboard into a live system once sensor hardware is attached. See [`backend/README.md`](backend/README.md). |
| [`firmware/`](firmware/duraknot_esp32.ino) | ESP32 sketch: rotary encoder for length/speed, vibration sensor for defect events, streams JSON at 1 Hz. |
| [`tests/`](tests/) | `test_oee.py` — 7 unit tests on the OEE formula (hand-calculated case, perfect line, availability-only loss, performance clamp, quality floor, insufficient-data guard, A×P×Q identity). `render_check.js` — headless jsdom harness that instruments every chart's canvas context and verifies all 6 charts draw and every DOM reference resolves. `validate_output_realism.js` — reproduces the submission's "five independent 20-minute runs" evidence on demand instead of leaving it as a frozen number in a slide. |
| [`submission.pdf`](submission.pdf) | The case study report as submitted. |

## Why a backend and firmware exist alongside a "zero-dependency" dashboard

The dashboard is deliberately standalone — it has to run at a venue with no network. The backend and firmware are what make the claims in the submission (`submission.pdf`) literally true rather than aspirational: a real Flask REST API, real SQLite persistence, a real ESP32 sketch, and a real, re-runnable test suite, all living in this repo rather than only described in a slide deck.

## Running things locally

```bash
# Dashboard — just open it, no build step
start index.html          # Windows
open index.html           # macOS

# OEE unit tests
pip install pytest
pytest tests/test_oee.py -v

# Render verification harness
cd tests && npm install && node render_check.js

# Reproduce the "five 20-minute runs" output-realism evidence
cd tests && node validate_output_realism.js

# Backend (turns the dashboard into a live system)
cd backend
pip install -r requirements.txt
python app.py
```

Then point the dashboard's Settings panel (⚙, top right) at the backend's URL to switch it from simulation to live data.

Tests run automatically on every push via [GitHub Actions](.github/workflows/test.yml).

## Limitations and next steps

- Simulated data only. The firmware and backend have not been validated with a real encoder and vibration sensor, so the live-data path is untested end to end.
- The OEE formula is unit-tested, but the benchmark values behind the simulator are indicative figures from public sources, not measurements from the Duraknot line.
- The dashboard is a single HTML file, which suits offline demos but is hard to extend.
- Next: run the firmware against a real line or a bench rig, compare simulator output with real readings, and recalibrate.
