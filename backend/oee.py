"""OEE (Overall Equipment Effectiveness) calculation.

Ported line-for-line from the dashboard's computeOEE() in index.html so the
backend, the frontend simulator and the test suite always agree on the
formula. Kept dependency-free on purpose.
"""

IDEAL_RATE_DEFAULT = 14.0  # m/min — entry/mid-band for welded wire mesh machines, see ../DATA_SOURCES.md


def compute_oee(planned_sec, run_sec, total_length_m, defect_events, ideal_rate=IDEAL_RATE_DEFAULT):
    """Mirrors the JS computeOEE(). Returns a dict, or None if not enough data yet.

    planned_sec:     total seconds the line has been monitored (running + stopped)
    run_sec:         seconds the line was actually running
    total_length_m:  total length produced so far, in metres
    defect_events:   count of defect events recorded so far
    ideal_rate:      ideal cycle rate, m/min
    """
    if planned_sec < 5:
        return None

    availability = run_sec / planned_sec if planned_sec > 0 else 0.0
    ideal_output = (run_sec / 60.0) * ideal_rate
    performance = min(total_length_m / ideal_output, 1.0) if ideal_output > 0 else 0.0
    avg_rate = total_length_m / (run_sec / 60.0) if run_sec > 0 else 0.0
    bad_length = min(defect_events * (avg_rate / 60.0), total_length_m)
    quality = (total_length_m - bad_length) / total_length_m if total_length_m > 0 else 0.0

    return {
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": availability * performance * quality,
        "runtime": run_sec,
        "planned": planned_sec,
        "ideal_output": ideal_output,
        "bad_length": bad_length,
        "avg_rate": avg_rate,
    }
