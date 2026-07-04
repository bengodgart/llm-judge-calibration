"""Load the labeled judge set and the pairwise position-bias set from JSONL.

The labeled set is one row per graded output:
    {"id", "category", "input", "output", "human_label", "judge_label",
     "judge_rationale"}
`human_label` and `judge_label` are the two verdicts to compare (for example
"pass" and "fail"). `judge_label` may be absent; if so the row is left pending
for the optional live judge run and is not scored offline.

The pairwise set is one row per A/B comparison, used only for the position-swap
probe:
    {"id", "input", "answer_a", "answer_b", "pick_original", "pick_swapped"}
`pick_original` is the answer the judge chose when shown order [a, b];
`pick_swapped` is what it chose when the two were swapped to [b, a]. Each is
"a" or "b" naming the stable content, so a differing pick is a position flip.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LabeledRow:
    id: str
    category: str
    input: str
    output: str
    human_label: str
    judge_label: str = ""           # "" means not yet judged
    judge_rationale: str = ""

    @property
    def judged(self) -> bool:
        return bool(self.judge_label)

    @property
    def agree(self) -> bool:
        return self.judged and self.human_label == self.judge_label


@dataclass
class PairwiseRow:
    id: str
    input: str
    answer_a: str
    answer_b: str
    pick_original: str
    pick_swapped: str

    @property
    def flipped(self) -> bool:
        return self.pick_original != self.pick_swapped


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for n, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path} line {n}: invalid JSON: {exc}") from exc
    return rows


def load_labeled(path: str) -> list[LabeledRow]:
    rows: list[LabeledRow] = []
    for row in _read_jsonl(path):
        rows.append(
            LabeledRow(
                id=str(row["id"]),
                category=str(row.get("category", "uncategorized")),
                input=str(row.get("input", "")),
                output=str(row.get("output", "")),
                human_label=str(row["human_label"]).strip(),
                judge_label=str(row.get("judge_label", "") or "").strip(),
                judge_rationale=str(row.get("judge_rationale", "")),
            )
        )
    if not rows:
        raise ValueError(f"no rows found in {path}")
    return rows


def load_pairwise(path: str) -> list[PairwiseRow]:
    rows: list[PairwiseRow] = []
    for row in _read_jsonl(path):
        rows.append(
            PairwiseRow(
                id=str(row["id"]),
                input=str(row.get("input", "")),
                answer_a=str(row.get("answer_a", "")),
                answer_b=str(row.get("answer_b", "")),
                pick_original=str(row["pick_original"]).strip().lower(),
                pick_swapped=str(row["pick_swapped"]).strip().lower(),
            )
        )
    return rows
