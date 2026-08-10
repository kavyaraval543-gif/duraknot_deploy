"""
Duraknot production monitoring backend.

Ingests one JSON reading per second -- either POSTed by an ESP32 over WiFi,
or read from USB serial (set SERIAL_PORT) straight from the sketch in
../firmware/duraknot_esp32.ino -- evaluates the same alert rules as the
dashboard's simulator, persists everything to SQLite, and serves the REST
API the dashboard's Settings modal points at.

Run:
    pip install -r requirements.txt
    python app.py                      # HTTP ingest only, port 5000
    SERIAL_PORT=COM5 python app.py     # also reads the ESP32 over USB serial

API:
    POST /api/ingest      body: {length_m, speed_mpm, status, defect, defect_type}
    GET  /api/kpis         -> {ready, length_m, speed_mpm, status, defect_total, ts}
    GET  /api/oee           -> full Availability/Performance/Quality/OEE breakdown
    GET  /api/alerts        -> alert log, newest first
    POST /api/shifts/end    -> persist current shift, then reset counters
    GET  /api/shifts        -> shift history, newest first
    GET  /api/health        -> {status: "ok"}
"""
import json
import os
import sqlite3
import threading
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

from oee import compute_oee

DB_PATH = os.environ.get("DURAKNOT_DB", os.path.join(os.path.dirname(__file__), "duraknot.db"))
IDEAL_RATE = 14.0
ROLLING_WINDOW = 90          # matches the dashboard's 90-reading rolling window
DEFECT_RATE_ALERT_THRESHOLD = 0.20
JAM_SPEED_RATIO = 0.5
ALERT_THROTTLE_SEC = 15

app = Flask(__name__)
CORS(app)

_lock = threading.Lock()


def _new_state():
    return {
        "planned_sec": 0, "run_sec": 0, "down_sec": 0,
        "total_length_m": 0.0, "defect_events": 0, "stoppages": 0,
        "last_status": "RUNNING", "status": "RUNNING",
        "speed_mpm": 0.0, "recent": [],  # list of {defect, status, speed_mpm}
        "alerts": [],  # newest first
        "_last_defect_alert": 0.0, "_last_speed_alert": 0.0,
        "started_at": None,
    }


state = _new_state()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL, length_m REAL, speed_mpm REAL, status TEXT,
            defect INTEGER, defect_type TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL, level TEXT, message TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at REAL, ended_at REAL,
            planned_sec INTEGER, run_sec INTEGER, down_sec INTEGER,
            total_length_m REAL, defect_events INTEGER, stoppages INTEGER,
            availability REAL, performance REAL, quality REAL, oee REAL
        )""")


def now():
    return time.time()


def add_alert(level, message):
    state["alerts"].insert(0, {"ts": now(), "level": level, "message": message})
    state["alerts"] = state["alerts"][:400]
    with db() as conn:
        conn.execute("INSERT INTO alerts (ts, level, message) VALUES (?, ?, ?)",
                      (state["alerts"][0]["ts"], level, message))


def check_alerts(reading):
    if reading["status"] == "STOPPED" and state["last_status"] == "RUNNING":
        state["stoppages"] += 1
        add_alert("critical", "Line STOPPED — possible jam or changeover. Downtime clock running.")
    if reading["status"] == "RUNNING" and state["last_status"] == "STOPPED":
        add_alert("info", "Line RESUMED production.")
    state["last_status"] = reading["status"]

    recent = state["recent"]
    if len(recent) >= 20:
        dr = sum(r["defect"] for r in recent) / len(recent)
        if dr > DEFECT_RATE_ALERT_THRESHOLD and now() - state["_last_defect_alert"] > ALERT_THROTTLE_SEC:
            state["_last_defect_alert"] = now()
            add_alert("warning", f"High defect rate: {dr*100:.0f}% of last {len(recent)}s flagged — "
                                  f"inspect weld quality / mesh spacing.")

    if len(recent) >= 15 and reading["status"] == "RUNNING":
        running_speeds = [r["speed_mpm"] for r in recent if r["status"] == "RUNNING"]
        if running_speeds:
            avg = sum(running_speeds) / len(running_speeds)
            if avg > 1 and reading["speed_mpm"] < avg * JAM_SPEED_RATIO and now() - state["_last_speed_alert"] > ALERT_THROTTLE_SEC:
                state["_last_speed_alert"] = now()
                add_alert("warning", f"Speed dropped to {reading['speed_mpm']:.1f} m/min "
                                      f"(avg {avg:.1f}) — possible line slowdown.")


def ingest_reading(reading):
    """reading: {length_m, speed_mpm, status, defect (0/1), defect_type}"""
    with _lock:
        if state["started_at"] is None:
            state["started_at"] = now()
        state["planned_sec"] += 1
        if reading["status"] == "RUNNING":
            state["run_sec"] += 1
        else:
            state["down_sec"] += 1
        state["total_length_m"] = reading["length_m"]
        state["speed_mpm"] = reading["speed_mpm"]
        state["status"] = reading["status"]
        if reading.get("defect"):
            state["defect_events"] += 1

        state["recent"].append({
            "defect": 1 if reading.get("defect") else 0,
            "status": reading["status"],
            "speed_mpm": reading["speed_mpm"],
        })
        state["recent"] = state["recent"][-ROLLING_WINDOW:]

        check_alerts(reading)

        with db() as conn:
            conn.execute(
                "INSERT INTO readings (ts, length_m, speed_mpm, status, defect, defect_type) VALUES (?,?,?,?,?,?)",
                (now(), reading["length_m"], reading["speed_mpm"], reading["status"],
                 1 if reading.get("defect") else 0, reading.get("defect_type")),
            )


def current_oee():
    return compute_oee(state["planned_sec"], state["run_sec"], state["total_length_m"],
                        state["defect_events"], IDEAL_RATE)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/ingest", methods=["POST"])
def api_ingest():
    body = request.get_json(force=True, silent=True)
    if not body or "length_m" not in body or "speed_mpm" not in body or "status" not in body:
        return jsonify({"error": "expected {length_m, speed_mpm, status, defect?, defect_type?}"}), 400
    ingest_reading(body)
    return jsonify({"ok": True})


@app.route("/api/kpis")
def api_kpis():
    with _lock:
        ready = state["started_at"] is not None
        return jsonify({
            "ready": ready,
            "length_m": state["total_length_m"],
            "speed_mpm": state["speed_mpm"],
            "status": state["status"],
            "defect_total": state["defect_events"],
            "ts": now(),
        })


@app.route("/api/oee")
def api_oee():
    with _lock:
        o = current_oee()
        if o is None:
            return jsonify({"ready": False})
        o["ready"] = True
        return jsonify(o)


@app.route("/api/alerts")
def api_alerts():
    with _lock:
        return jsonify({
            "alerts": state["alerts"],
            "stoppages": state["stoppages"],
            "down_sec": state["down_sec"],
        })


@app.route("/api/shifts", methods=["GET"])
def api_shifts_list():
    with db() as conn:
        rows = conn.execute("SELECT * FROM shifts ORDER BY ended_at DESC").fetchall()
        return jsonify([dict(r) for r in rows])


@app.route("/api/shifts/end", methods=["POST"])
def api_shifts_end():
    with _lock:
        o = current_oee() or {"availability": 0, "performance": 0, "quality": 0, "oee": 0}
        record = {
            "started_at": state["started_at"] or now(),
            "ended_at": now(),
            "planned_sec": state["planned_sec"],
            "run_sec": state["run_sec"],
            "down_sec": state["down_sec"],
            "total_length_m": state["total_length_m"],
            "defect_events": state["defect_events"],
            "stoppages": state["stoppages"],
            "availability": o["availability"],
            "performance": o["performance"],
            "quality": o["quality"],
            "oee": o["oee"],
        }
        with db() as conn:
            cur = conn.execute(
                """INSERT INTO shifts (started_at, ended_at, planned_sec, run_sec, down_sec,
                   total_length_m, defect_events, stoppages, availability, performance, quality, oee)
                   VALUES (:started_at,:ended_at,:planned_sec,:run_sec,:down_sec,
                   :total_length_m,:defect_events,:stoppages,:availability,:performance,:quality,:oee)""",
                record,
            )
            record["id"] = cur.lastrowid
        state.clear()
        state.update(_new_state())
        return jsonify(record)


def _serial_reader_thread(port, baud=115200):
    """Optional: reads JSON lines straight from the ESP32 sketch over USB
    serial and ingests them in-process. Enabled via SERIAL_PORT env var so
    the backend can ingest without any WiFi/HTTP hop from the device."""
    import serial  # pyserial -- only imported if this thread actually starts
    with serial.Serial(port, baud, timeout=2) as ser:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                reading = json.loads(line)
            except ValueError:
                continue
            ingest_reading(reading)


init_db()

if __name__ == "__main__":
    serial_port = os.environ.get("SERIAL_PORT")
    if serial_port:
        t = threading.Thread(target=_serial_reader_thread, args=(serial_port,), daemon=True)
        t.start()
        print(f"Reading ESP32 telemetry from serial port {serial_port}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
