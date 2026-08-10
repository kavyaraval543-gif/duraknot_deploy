# Duraknot Production Intelligence Dashboard

IoT-enabled production monitoring for the Duraknot fence-roll line — A-1 Launchpad 2026, Automation & Robotics Case Study 2. Team Forest.AI (Ayush Jha, Kavya Raval), MPSTME, NMIMS University.

**Live dashboard:** https://duraknotdashboard.vercel.app

## What's here

| Path | What it is |
|---|---|
| [`index.html`](index.html) | The dashboard itself. Single file, zero dependencies, runs offline. Ships with a built-in simulator so it's always demonstrable, and auto-detects a live backend if one is reachable (see the ⚙ Settings panel). |
| [`backend/`](backend/) | Flask REST API + SQLite persistence + alert engine that turns the dashboard into a live system once sensor hardware is attached. See [`backend/README.md`](backend/README.md). |
| [`firmware/`](firmware/duraknot_esp32.ino) | ESP32 sketch: rotary encoder for length/speed, vibration sensor for defect events, streams JSON at 1 Hz. |
| [`tests/`](tests/) | `test_oee.py` — 7 unit tests on the OEE formula (hand-calculated case, perfect line, availability-only loss, performance clamp, quality floor, insufficient-data guard, A×P×Q identity). `render_check.js` — headless jsdom harness that instruments every chart's canvas context and verifies all 6 charts draw and every DOM reference resolves. |
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

# Backend (turns the dashboard into a live system)
cd backend
pip install -r requirements.txt
python app.py
```

Then point the dashboard's Settings panel (⚙, top right) at the backend's URL to switch it from simulation to live data.

Tests run automatically on every push via [GitHub Actions](.github/workflows/test.yml).
