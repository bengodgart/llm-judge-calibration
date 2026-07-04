"""End-to-end tests over the bundled sample set. These pin the headline numbers."""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from judgecal.calibrate import calibrate
from judgecal.dataset import load_labeled, load_pairwise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELED = os.path.join(ROOT, "data", "labeled_sample.jsonl")
PAIRWISE = os.path.join(ROOT, "data", "pairwise_sample.jsonl")


def _cal():
    rows = load_labeled(LABELED)
    pairs = load_pairwise(PAIRWISE)
    return calibrate(rows, pairwise=pairs)


def test_sample_loads_sixty_rows():
    rows = load_labeled(LABELED)
    assert len(rows) == 60
    cats = {r.category for r in rows}
    assert cats == {"factual_qa", "math", "summarization", "refusals"}


def test_overall_agreement_and_kappa():
    cal = _cal()
    assert cal.n == 60
    # 48 of 60 agree -> 80 percent raw agreement.
    assert math.isclose(cal.accuracy, 0.80, rel_tol=1e-9)
    # kappa = (0.8 - 0.52) / (1 - 0.52) = 0.5833...
    assert math.isclose(cal.kappa, 0.28 / 0.48, rel_tol=1e-6)
    assert cal.band == "moderate"


def test_accuracy_ci_brackets_the_point_estimate():
    cal = _cal()
    assert cal.accuracy_ci.low < cal.accuracy < cal.accuracy_ci.high
    assert math.isclose(cal.accuracy_ci.low, 0.682, abs_tol=0.01)
    assert math.isclose(cal.accuracy_ci.high, 0.882, abs_tol=0.01)


def test_refusals_is_the_unreliable_category():
    cal = _cal()
    by_name = {c.name: c for c in cal.categories}
    refusals = by_name["refusals"]
    assert refusals.kappa < 0.0                       # worse than chance
    assert not refusals.reliable


def test_reliable_categories_named():
    cal = _cal()
    reliable = {c.name for c in cal.reliable_categories}
    # factual_qa and math are the clear reliable ones
    assert "factual_qa" in reliable
    assert "math" in reliable
    assert "refusals" not in reliable


def test_verdict_has_at_least_one_each_side():
    cal = _cal()
    assert cal.reliable_categories, "expected at least one reliable category"
    assert cal.unreliable_categories, "expected at least one unreliable category"


def test_position_flip_rate_matches_fixture():
    cal = _cal()
    assert cal.position is not None
    assert cal.position.n == 12
    assert cal.position.flips == 4
    assert math.isclose(cal.position.flip_rate, 4 / 12, rel_tol=1e-9)


def test_verbosity_probe_present():
    cal = _cal()
    assert cal.verbosity.n == 60
    # the correlation is whatever the data says; just confirm it computed a finite value
    assert -1.0 <= cal.verbosity.correlation <= 1.0
