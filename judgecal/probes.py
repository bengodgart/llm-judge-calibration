"""Two bias probes for an LLM-as-judge.

Position or order bias: present a pair of answers in both orders and measure how
often the judge's pick changes. A judge that agrees with itself should pick the
same answer regardless of order, so a nonzero flip rate is order sensitivity.

Verbosity bias: correlate the length of the judged output with the judge's
verdict. A positive correlation means the judge tends to pass longer answers,
which is the well-documented tendency of LLM judges to reward length over
substance.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dataset import LabeledRow, PairwiseRow
from .metrics import pearson


@dataclass
class PositionProbe:
    n: int
    flips: int
    first_position_wins: int        # flips where the judge chose the first-shown answer both times

    @property
    def flip_rate(self) -> float:
        return (self.flips / self.n) if self.n else 0.0


@dataclass
class VerbosityProbe:
    n: int
    correlation: float
    mean_len_pass: float
    mean_len_fail: float


def position_probe(rows: list[PairwiseRow]) -> PositionProbe:
    n = len(rows)
    flips = sum(1 for r in rows if r.flipped)
    # A first-position flip: order [a,b] picked a (the first shown), and after the
    # swap to [b,a] it picked b (again the first shown). That is pure order bias.
    first_pos = sum(
        1 for r in rows if r.flipped and r.pick_original == "a" and r.pick_swapped == "b"
    )
    return PositionProbe(n=n, flips=flips, first_position_wins=first_pos)


def verbosity_probe(rows: list[LabeledRow], positive_label: str = "pass") -> VerbosityProbe:
    judged = [r for r in rows if r.judged]
    lengths = [float(len(r.output)) for r in judged]
    scores = [1.0 if r.judge_label == positive_label else 0.0 for r in judged]
    corr = pearson(lengths, scores)
    pass_lens = [len(r.output) for r in judged if r.judge_label == positive_label]
    fail_lens = [len(r.output) for r in judged if r.judge_label != positive_label]
    mean_pass = sum(pass_lens) / len(pass_lens) if pass_lens else 0.0
    mean_fail = sum(fail_lens) / len(fail_lens) if fail_lens else 0.0
    return VerbosityProbe(
        n=len(judged), correlation=corr, mean_len_pass=mean_pass, mean_len_fail=mean_fail
    )
