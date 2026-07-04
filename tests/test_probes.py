"""Tests for the position and verbosity bias probes."""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from judgecal.dataset import LabeledRow, PairwiseRow
from judgecal.probes import position_probe, verbosity_probe


def _pair(pid, orig, swap):
    return PairwiseRow(id=pid, input="", answer_a="", answer_b="", pick_original=orig, pick_swapped=swap)


def test_position_flip_rate_hand_count():
    # 12 pairs, 4 of them flip a -> b. flip rate = 4/12.
    rows = [_pair(f"c{i}", "a", "a") for i in range(4)]
    rows += [_pair(f"d{i}", "b", "b") for i in range(4)]
    rows += [_pair(f"f{i}", "a", "b") for i in range(4)]
    probe = position_probe(rows)
    assert probe.n == 12
    assert probe.flips == 4
    assert math.isclose(probe.flip_rate, 4 / 12, rel_tol=1e-9)
    # all four flips favored the first-shown answer
    assert probe.first_position_wins == 4


def test_position_no_flips():
    rows = [_pair("a", "a", "a"), _pair("b", "b", "b")]
    probe = position_probe(rows)
    assert probe.flips == 0
    assert probe.flip_rate == 0.0


def test_verbosity_correlation_longer_passes():
    # Longer outputs are passed, shorter failed -> positive correlation.
    rows = [
        LabeledRow(id="1", category="c", input="", output="x" * 10, human_label="fail", judge_label="fail"),
        LabeledRow(id="2", category="c", input="", output="x" * 20, human_label="fail", judge_label="fail"),
        LabeledRow(id="3", category="c", input="", output="x" * 80, human_label="pass", judge_label="pass"),
        LabeledRow(id="4", category="c", input="", output="x" * 90, human_label="pass", judge_label="pass"),
    ]
    probe = verbosity_probe(rows)
    assert probe.n == 4
    assert probe.correlation > 0.9
    assert probe.mean_len_pass > probe.mean_len_fail


def test_verbosity_ignores_pending_rows():
    rows = [
        LabeledRow(id="1", category="c", input="", output="short", human_label="pass", judge_label="pass"),
        LabeledRow(id="2", category="c", input="", output="unjudged", human_label="pass", judge_label=""),
    ]
    probe = verbosity_probe(rows)
    assert probe.n == 1
