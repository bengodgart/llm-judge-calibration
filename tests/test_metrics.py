"""Unit tests for the hand-rolled statistics. Pytest, no third-party deps."""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from judgecal.metrics import (
    accuracy,
    cohen_kappa,
    kappa_band,
    pearson,
    wilson_interval,
)


def test_accuracy_simple():
    pairs = [("pass", "pass"), ("pass", "fail"), ("fail", "fail"), ("fail", "fail")]
    assert accuracy(pairs) == 0.75


def test_kappa_perfect_agreement():
    pairs = [("pass", "pass"), ("fail", "fail"), ("pass", "pass"), ("fail", "fail")]
    assert cohen_kappa(pairs) == 1.0


def test_kappa_hand_worked_example():
    # 10 items. Confusion: pass/pass=5, fail/fail=3, human pass judge fail=1,
    # human fail judge pass=1. po = 8/10 = 0.8.
    # human: pass=6, fail=4. judge: pass=6, fail=4.
    # pe = 0.6*0.6 + 0.4*0.4 = 0.36 + 0.16 = 0.52.
    # kappa = (0.8 - 0.52) / (1 - 0.52) = 0.28 / 0.48 = 0.5833...
    pairs = (
        [("pass", "pass")] * 5
        + [("fail", "fail")] * 3
        + [("pass", "fail")]
        + [("fail", "pass")]
    )
    assert math.isclose(cohen_kappa(pairs), 0.28 / 0.48, rel_tol=1e-9)


def test_kappa_worse_than_chance_is_negative():
    # A judge that systematically disagrees can score below zero.
    pairs = (
        [("pass", "fail")] * 4
        + [("fail", "pass")] * 4
        + [("pass", "pass")] * 2
        + [("fail", "fail")] * 2
    )
    k = cohen_kappa(pairs)
    assert k < 0.0
    assert math.isclose(k, -1.0 / 3.0, rel_tol=1e-9)


def test_wilson_interval_hand_values():
    # n=60, 48 successes (p=0.8). Wilson 95% CI is about [0.682, 0.882].
    ci = wilson_interval(48, 60)
    assert math.isclose(ci.low, 0.682, abs_tol=0.005)
    assert math.isclose(ci.high, 0.882, abs_tol=0.005)
    assert ci.low < 0.8 < ci.high


def test_wilson_interval_stays_in_unit_range():
    ci = wilson_interval(10, 10)
    assert 0.0 <= ci.low <= 1.0
    assert 0.0 <= ci.high <= 1.0
    assert ci.high <= 1.0


def test_pearson_perfect_positive():
    assert math.isclose(pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0, rel_tol=1e-9)


def test_pearson_flat_series_is_zero():
    assert pearson([1, 1, 1], [2, 5, 9]) == 0.0


def test_kappa_band_labels():
    assert kappa_band(-0.1) == "worse than chance"
    assert kappa_band(0.5) == "moderate"
    assert kappa_band(0.7) == "substantial"
    assert kappa_band(0.9) == "almost perfect"
