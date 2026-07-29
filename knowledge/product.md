---
type: Product
title: llm-judge-calibration
description: 'Checks whether an LLM-as-judge actually agrees with a human before you trust it as an auto-grader: Cohen kappa overall and per category, accuracy with a 95 percent confidence interval, position and verbosity bias probes, and a reliable-for-X-not-Y verdict.'
domain: AI & LLM Tooling
users: 'Teams using an LLM as an auto-grader who have never checked it against human labels.'
lifecycle: 'shipped. Published on GitHub as a CLI; there is no hosted version.'
pricing: 'Free. MIT licensed, no API key and no cost to run.'
generated:
  by: claude-opus-5
  at: '2026-07-29T05:00:00+00:00'
status: stable
resource: https://github.com/bengodgart/llm-judge-calibration.git
---

# llm-judge-calibration

Checks whether an LLM-as-judge actually agrees with a human before you trust it as an
auto-grader: Cohen kappa overall and per category, accuracy with a 95 percent confidence
interval, position and verbosity bias probes, and a reliable-for-X-not-Y verdict.

## Who it is for

Teams using an LLM as an auto-grader who have never checked it against human labels.

## What problem it solves

Everyone says they use LLM-as-judge. Almost nobody has checked whether their judge agrees
with a human, and a single accuracy figure hides the thing you need to know.

On the bundled set the judge looks fine at 80 percent raw agreement. The per-category
breakdown shows it is almost perfect on factual QA and maths and actively wrong on refusals,
where it scores worse than chance: it fails correct, safe refusals and passes harmful
compliance. One number hides that; the calibration surfaces it.

Two bias probes come with it. Position bias shows the judge the same pair in both orders and
counts how often its pick changes, which is order sensitivity rather than judgment. Verbosity
bias correlates output length against a pass verdict. On the bundled set that correlation is
near zero, and reporting the null is part of the point: not every bias is present, and you
should measure rather than assume.

## The reliability gate

A category is called reliable only when Cohen kappa is at least the threshold, 0.60 by
default, **and** it has at least a minimum number of items, 8 by default. That second
condition exists so a handful of lucky agreements never earns a reliable stamp. Everything
else is flagged not reliable with the reason shown.

## Current state

Shipped and public on GitHub. Version 0.1.0. `--min-kappa` makes it exit non-zero when
overall kappa falls below a gate, so a rubric change that quietly degrades agreement can fail
a build.
