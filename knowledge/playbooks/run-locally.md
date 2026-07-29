---
type: Playbook
title: Run llm-judge-calibration locally
description: 'How to calibrate an LLM judge against human labels on a dev machine.'
generated:
  by: claude-opus-5
  at: '2026-07-29T04:31:42+00:00'
status: stable
---

# Steps

Python 3.9 or newer. Standard library only, so there is nothing to install.

1. `git clone https://github.com/bengodgart/llm-judge-calibration`
2. `cd llm-judge-calibration`
3. `python -m judgecal calibrate --labeled data/labeled_sample.jsonl --pairwise data/pairwise_sample.jsonl`

Add `--html report.html --md report.md` to write the report files.

## Scoring your own judge

```
python -m judgecal calibrate --labeled your_data.jsonl --html report.html
```

Add `--min-kappa 0.6` to exit non-zero when overall kappa falls below a gate.

## Tests

```
python -m pytest -q   # 21 tests, no third-party runtime deps
```

## Common failures

* **A category with too few items is never called reliable**, however high its kappa. The
  default minimum is 8, tunable with `--min-category-n`. That is the gate working.
* **Kappa below zero is not a bug.** Kappa corrects for chance agreement, so a judge that is
  anti-correlated with the human scores negative even at 33 percent raw agreement.
* **The position probe needs the pairwise file.** Without `--pairwise` there is no order-bias
  section.
