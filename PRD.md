# PRD — llm-judge-calibration

**One-liner (from brief 07):** A free harness that calibrates an LLM-as-judge against human labels. It scores the judge's recorded verdicts over a labeled set, reports agreement (Cohen's kappa plus raw accuracy), probes for position and verbosity bias, and emits an honest "reliable for X, not for Y" verdict, for anyone who uses LLM-as-judge in evals but has never checked whether their judge actually agrees with a human.

**Usefulness (from brief 07):** LLM-as-judge is everywhere; a calibrated one is almost nowhere. The evals hiring research ranks the judge-versus-human calibration writeup as the single rarest high-signal evals artifact, the one screeners probe for and the pile never has. Useful to one eval engineer on day one: point it at a JSONL of graded outputs, get back whether that judge can be trusted, before shipping it as an auto-grader. Ships with a bundled sample set so a stranger sees a real calibration report in under two minutes with no data of their own.

## Features traced to the brief

| Brief v1 scope item | Where it lives |
|---|---|
| 1. Load a labeled JSONL of `{id, input, output, human_label, judge_label?, judge_rationale?}`; score pre-recorded judge labels at $0 | `judgecal/dataset.py` (`load_labeled`), `judgecal/calibrate.py` |
| 1. Optional `--run-judge` with a rubric prompt and the user's own key when `judge_label` is absent | `judgecal/judge.py`, wired in `judgecal/cli.py`, off by default |
| 2. Agreement metrics: raw accuracy, Cohen's kappa, per-category confusion | `judgecal/metrics.py` (`accuracy`, `cohen_kappa`, `confusion`), `judgecal/calibrate.py` |
| 3a. Position or order bias: swap A/B, measure flip rate | `judgecal/probes.py` (`position_probe`), pairwise loader in `dataset.py` |
| 3b. Verbosity bias: correlation between output length and judge score | `judgecal/probes.py` (`verbosity_probe`), `metrics.pearson` |
| 4. Verdict block naming reliable and not-reliable categories with visible thresholds, plus a 95 percent CI on accuracy | `judgecal/calibrate.py` (reliability rule), `metrics.wilson_interval`, `report.py` |
| 5. One committed report (HTML + md) with numbers, disagreement examples, and the verdict; README opens with the headline number | `examples/sample-report.html`, `examples/sample-report.md`, `README.md` |

## Statistics, hand-rolled (brief: prefer stdlib, implement kappa and CI by hand)

- **Cohen's kappa** computed directly from the confusion of the two raters, corrected for chance agreement.
- **95 percent confidence interval** via the Wilson score interval, chosen over the normal approximation because it stays inside [0, 1] at small n and near the extremes.
- **Pearson correlation** for the verbosity probe, hand-rolled so there is no numpy or scikit-learn dependency.
- Zero third-party runtime dependencies. Python 3.9+.

## $0 and offline (brief: non-negotiable)

The default path scores already-recorded judge labels, so it never calls an API. The single optional `--run-judge` path uses the builder's own key and is off by default, is imported lazily, and is never touched by the tests or the offline calibration.

## Non-goals (NOT v1, from the brief, parked)

- A hosted dashboard, accounts, a judge marketplace.
- Auto-fixing or auto-suggesting the rubric from disagreements.
- Multi-provider judge routing; live judge re-runs beyond the single `--run-judge` path.
- Storing anyone's data.

## Demo path (stranger sees value in under two minutes)

Clone, run one command on the bundled set, see 80 percent raw agreement but kappa -0.33 on refusals, the per-category verdict that is the point. Then score their own judge's JSONL.

## Done when

- The CLI produces a calibration report on the bundled set in seconds for a stranger who just cloned it.
- Kappa and the position-swap flip rate match a hand-checked spot example (see EVIDENCE.md).
- The verdict block names at least one reliable and one not-reliable category with visible thresholds.
- README opens with the headline number; copy passes the no-em-dash sweep. Repo public, MIT, runs at $0 with the judge re-run off.
