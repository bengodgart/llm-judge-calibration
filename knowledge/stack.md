---
type: Tech Stack
title: llm-judge-calibration stack
description: 'Frameworks, storage and services llm-judge-calibration runs on.'
runtime: 'Python 3.9 or newer'
framework: 'None. Standard library only, including the statistics.'
dependencies: 'None at runtime.'
build: 'setuptools. Installable, but it also runs straight from a clone.'
entry_point: 'judgecal, or python -m judgecal'
network: 'None. No API key, fully offline.'
tests: 'python -m pytest -q, 21 tests'
generated:
  by: claude-opus-5
  at: '2026-07-29T04:31:42+00:00'
status: stable
---

# Stack

* **Runtime**: Python 3.9 or newer.
* **Dependencies**: none at runtime. Cohen kappa and the Wilson confidence interval are
  hand-rolled rather than pulled from a stats library.
* **Build backend**: setuptools, declared in `pyproject.toml`. The package is `judgecal`.
* **Entry point**: the `judgecal` console script, or `python -m judgecal` from a clone.
* **Network**: none. No API key, no cost.
* **Tests**: `python -m pytest -q`, 21 tests, no third-party runtime dependencies.

## Input formats

* **Labeled JSONL**, one graded output per line, with `id`, `category`, `input`, `output`,
  `human_label`, `judge_label` and an optional `judge_rationale`. Any label set works, not
  just pass and fail.
* **Pairwise JSONL** (optional, needed only for the position probe), one A/B comparison per
  line with `id`, `input`, `answer_a`, `answer_b`, `pick_original` and `pick_swapped`. Each
  pick names the stable content, so a differing pick is a genuine position flip.

## Notes

`--kappa-threshold` and `--min-category-n` tune the reliability gate. `--html` and `--md`
write report files; a committed sample report is in `examples/`.
