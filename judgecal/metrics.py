"""Deterministic agreement statistics, hand-rolled on the standard library.

No numpy, no scikit-learn. Cohen's kappa, a Wilson 95 percent confidence
interval for a proportion, and Pearson correlation are implemented directly so
the math is auditable and the tool has zero dependencies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Interval:
    low: float
    high: float


def accuracy(pairs: list[tuple[str, str]]) -> float:
    """Fraction of (human, judge) pairs that agree."""
    if not pairs:
        return 0.0
    agree = sum(1 for h, j in pairs if h == j)
    return agree / len(pairs)


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    """Cohen's kappa for two raters over the same items.

    kappa = (po - pe) / (1 - pe), where po is observed agreement and pe is the
    agreement expected if each rater assigned labels independently at their own
    base rates. Returns 1.0 when both raters are perfectly and identically
    constant (pe == 1), the conventional degenerate case.
    """
    n = len(pairs)
    if n == 0:
        return 0.0
    labels = {h for h, _ in pairs} | {j for _, j in pairs}
    po = accuracy(pairs)
    pe = 0.0
    for label in labels:
        p_human = sum(1 for h, _ in pairs if h == label) / n
        p_judge = sum(1 for _, j in pairs if j == label) / n
        pe += p_human * p_judge
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


def wilson_interval(successes: int, n: int, z: float = 1.96) -> Interval:
    """Wilson score 95 percent CI for a binomial proportion.

    Preferred over the normal approximation because it stays inside [0, 1] and
    behaves at small n and proportions near 0 or 1.
    """
    if n == 0:
        return Interval(0.0, 0.0)
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))) / denom
    return Interval(max(0.0, center - margin), min(1.0, center + margin))


def pearson(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation coefficient. Returns 0.0 if either series is flat."""
    n = len(xs)
    if n == 0 or n != len(ys):
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def kappa_band(kappa: float) -> str:
    """Landis and Koch descriptive band for a kappa value."""
    if kappa < 0.0:
        return "worse than chance"
    if kappa < 0.21:
        return "slight"
    if kappa < 0.41:
        return "fair"
    if kappa < 0.61:
        return "moderate"
    if kappa < 0.81:
        return "substantial"
    return "almost perfect"


def confusion(pairs: list[tuple[str, str]], labels: list[str]) -> dict[tuple[str, str], int]:
    """Counts keyed by (human_label, judge_label) over the given label set."""
    counts: dict[tuple[str, str], int] = {(h, j): 0 for h in labels for j in labels}
    for h, j in pairs:
        counts[(h, j)] = counts.get((h, j), 0) + 1
    return counts
