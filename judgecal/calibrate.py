"""Assemble a full calibration from a labeled set and an optional pairwise set.

Overall agreement (accuracy, Wilson CI, kappa), a per-category breakdown with
its own kappa and confusion counts, the two bias probes, and a verdict that
names the categories the judge is reliable on and the ones it is not, using a
visible kappa threshold.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .dataset import LabeledRow, PairwiseRow
from .metrics import (
    Interval,
    accuracy,
    cohen_kappa,
    confusion,
    kappa_band,
    wilson_interval,
)
from .probes import (
    PositionProbe,
    VerbosityProbe,
    position_probe,
    verbosity_probe,
)


@dataclass
class CategoryResult:
    name: str
    n: int
    accuracy: float
    kappa: float
    confusion: dict[tuple[str, str], int]
    reliable: bool

    @property
    def band(self) -> str:
        return kappa_band(self.kappa)


@dataclass
class Disagreement:
    id: str
    category: str
    input: str
    output: str
    human_label: str
    judge_label: str
    judge_rationale: str


@dataclass
class Calibration:
    n: int
    labels: list[str]
    accuracy: float
    accuracy_ci: Interval
    kappa: float
    kappa_threshold: float
    min_category_n: int
    categories: list[CategoryResult]
    position: PositionProbe | None
    verbosity: VerbosityProbe
    disagreements: list[Disagreement]
    pending: int                    # rows with no judge_label (not scored offline)

    @property
    def band(self) -> str:
        return kappa_band(self.kappa)

    @property
    def reliable_categories(self) -> list[CategoryResult]:
        return [c for c in self.categories if c.reliable]

    @property
    def unreliable_categories(self) -> list[CategoryResult]:
        return [c for c in self.categories if not c.reliable]


def _pairs(rows: list[LabeledRow]) -> list[tuple[str, str]]:
    return [(r.human_label, r.judge_label) for r in rows]


def calibrate(
    rows: list[LabeledRow],
    pairwise: list[PairwiseRow] | None = None,
    kappa_threshold: float = 0.6,
    min_category_n: int = 8,
    positive_label: str = "pass",
) -> Calibration:
    judged = [r for r in rows if r.judged]
    pending = len(rows) - len(judged)
    labels = sorted({r.human_label for r in judged} | {r.judge_label for r in judged})

    pairs = _pairs(judged)
    acc = accuracy(pairs)
    n = len(judged)
    ci = wilson_interval(sum(1 for h, j in pairs if h == j), n)
    kappa = cohen_kappa(pairs)

    by_cat: dict[str, list[LabeledRow]] = {}
    for r in judged:
        by_cat.setdefault(r.category, []).append(r)

    categories: list[CategoryResult] = []
    for name in sorted(by_cat):
        crows = by_cat[name]
        cpairs = _pairs(crows)
        ck = cohen_kappa(cpairs)
        # Reliable only when the category is both large enough to trust and above
        # the kappa threshold. A tiny category is reported but never called
        # reliable on the strength of a handful of items.
        reliable = len(crows) >= min_category_n and ck >= kappa_threshold
        categories.append(
            CategoryResult(
                name=name,
                n=len(crows),
                accuracy=accuracy(cpairs),
                kappa=ck,
                confusion=confusion(cpairs, labels),
                reliable=reliable,
            )
        )
    # weakest first, so the problem categories lead the eye
    categories.sort(key=lambda c: c.kappa)

    disagreements = [
        Disagreement(
            id=r.id,
            category=r.category,
            input=r.input,
            output=r.output,
            human_label=r.human_label,
            judge_label=r.judge_label,
            judge_rationale=r.judge_rationale,
        )
        for r in judged
        if not r.agree
    ]

    pos = position_probe(pairwise) if pairwise else None
    verb = verbosity_probe(judged, positive_label=positive_label)

    return Calibration(
        n=n,
        labels=labels,
        accuracy=acc,
        accuracy_ci=ci,
        kappa=kappa,
        kappa_threshold=kappa_threshold,
        min_category_n=min_category_n,
        categories=categories,
        position=pos,
        verbosity=verb,
        disagreements=disagreements,
        pending=pending,
    )
