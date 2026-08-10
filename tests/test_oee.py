"""Seven OEE-correctness tests, as named in the A-1 Launchpad submission:
hand-calculated case, perfect line, availability-only loss, performance
clamp, quality floor, insufficient-data guard, and an A x P x Q identity
check. Run with: pytest tests/test_oee.py
"""
import random

import pytest
from oee import compute_oee


def test_hand_calculated_case():
    # 80s run / 100s planned, 16m actual vs 18.67m ideal, 14m good of 16m total
    o = compute_oee(planned_sec=100, run_sec=80, total_length_m=16, defect_events=10)
    assert o["availability"] == pytest.approx(0.80, abs=1e-4)
    assert o["performance"] == pytest.approx(0.857142857, abs=1e-4)
    assert o["quality"] == pytest.approx(0.875, abs=1e-4)
    assert o["oee"] == pytest.approx(0.60, abs=1e-4)


def test_perfect_line():
    # runs the whole planned window at exactly the ideal rate with zero defects
    ideal_output = (100 / 60.0) * 14.0
    o = compute_oee(planned_sec=100, run_sec=100, total_length_m=ideal_output, defect_events=0)
    assert o["availability"] == pytest.approx(1.0)
    assert o["performance"] == pytest.approx(1.0)
    assert o["quality"] == pytest.approx(1.0)
    assert o["oee"] == pytest.approx(1.0)


def test_availability_only_loss():
    # half the planned time was downtime; performance and quality are perfect
    # for the time it did run, so OEE should equal availability alone
    ideal_output = (50 / 60.0) * 14.0
    o = compute_oee(planned_sec=100, run_sec=50, total_length_m=ideal_output, defect_events=0)
    assert o["availability"] == pytest.approx(0.5)
    assert o["performance"] == pytest.approx(1.0)
    assert o["quality"] == pytest.approx(1.0)
    assert o["oee"] == pytest.approx(0.5)


def test_performance_clamp():
    # output exceeds the theoretical ideal (sensor noise / burst) -- performance
    # must clamp at 100%, never exceed it
    o = compute_oee(planned_sec=100, run_sec=60, total_length_m=30, defect_events=0)
    assert o["performance"] == pytest.approx(1.0)
    assert o["oee"] == pytest.approx(0.6)  # availability(0.6) x 1.0 x 1.0


def test_quality_floor():
    # an implausibly large defect count would make "bad length" exceed total
    # output -- quality must floor at 0%, never go negative
    o = compute_oee(planned_sec=100, run_sec=80, total_length_m=10, defect_events=1000)
    assert o["quality"] == pytest.approx(0.0)
    assert o["oee"] == pytest.approx(0.0)


def test_insufficient_data_guard():
    # fewer than 5 seconds of planned time -- not enough to report a figure
    assert compute_oee(planned_sec=0, run_sec=0, total_length_m=0, defect_events=0) is None
    assert compute_oee(planned_sec=4, run_sec=4, total_length_m=1, defect_events=0) is None


def test_identity_oee_equals_availability_times_performance_times_quality():
    rng = random.Random(42)
    for _ in range(500):
        planned = rng.randint(5, 5000)
        run = rng.randint(0, planned)
        total = rng.uniform(0, 2000)
        defects = rng.randint(0, 200)
        o = compute_oee(planned_sec=planned, run_sec=run, total_length_m=total, defect_events=defects)
        assert o["oee"] == pytest.approx(o["availability"] * o["performance"] * o["quality"], abs=1e-9)
