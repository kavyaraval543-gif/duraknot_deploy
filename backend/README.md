# Duraknot backend

Flask REST API + SQLite persistence + alert engine for the Duraknot dashboard.
The dashboard (`../index.html`) runs entirely standalone with a built-in
simulator; this backend is what turns it into a live system once real
sensor hardware (`../firmware/duraknot_esp32.ino`) is attached.

## Run

```bash
pip install -r requirements.txt
python app.py                      # HTTP ingest only, listens on :5000
SERIAL_PORT=COM5 python app.py     # also reads the ESP32 over USB serial
```

Then in the dashboard's Settings panel, point "Backend URL" at
`http://<this-machine>:5000` (or a tunnel URL if the dashboard is the
Vercel-hosted copy and the backend is on a different machine/network).

## Getting data in

- **USB serial (default for the shipped firmware):** set `SERIAL_PORT` to
  the ESP32's port before starting `app.py`; it reads the 1 Hz JSON lines
  the sketch prints and ingests them directly, no extra process needed.
- **WiFi:** uncomment `ENABLE_WIFI` in the `.ino` sketch and point
  `INGEST_URL` at `http://<this-machine>:5000/api/ingest`.
- **Manual / testing:** `POST /api/ingest` with
  `{"length_m":123.4,"speed_mpm":12.3,"status":"RUNNING","defect":0,"defect_type":null}`.

## API

| Endpoint | Method | Returns |
|---|---|---|
| `/api/health` | GET | `{status:"ok"}` |
| `/api/ingest` | POST | ingest one reading, `{ok:true}` |
| `/api/kpis` | GET | `{ready, length_m, speed_mpm, status, defect_total, ts}` — same shape the dashboard's simulator produces |
| `/api/oee` | GET | `{availability, performance, quality, oee, ...}` |
| `/api/alerts` | GET | `{alerts, stoppages, down_sec}`, newest alert first |
| `/api/shifts/end` | POST | persists the current shift, resets counters, returns the saved record |
| `/api/shifts` | GET | shift history, newest first |

All state lives in `duraknot.db` (SQLite, created on first run) plus an
in-memory snapshot for the alert-throttling logic. The OEE formula in
`oee.py` is the same one the dashboard uses and the same one `../tests/test_oee.py`
verifies against — one implementation, tested once, trusted everywhere.
