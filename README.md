# llm-judge-calibration

**Cohen's kappa 0.58 on the bundled set. Moderate overall, almost perfect on factual QA and math, and worse than chance on refusals.** A free harness that checks whether an LLM-as-judge actually agrees with a human before you trust it as an auto-grader.

Everyone says "I use LLM-as-judge." Almost nobody has checked whether their judge agrees with a human. This tool does exactly that. Point it at a JSONL of graded outputs with both a human label and the judge's label, and it reports the agreement, probes for two classic judge biases, and ends with an honest verdict: the categories where the judge is reliable enough to ship, and the ones where it is not.

The headline number is the point. A single accuracy figure hides the thing you need to know. On the bundled set the judge looks fine at 80 percent raw agreement, until the breakdown shows it is almost perfect on facts and math and actively wrong on refusals: it fails correct, safe refusals and passes harmful compliance. That is exactly the "reliable for X, not for Y" judgment the job hires for.

## What the report looks like

```
$ python -m judgecal calibrate --labeled data/labeled_sample.jsonl --pairwise data/pairwise_sample.jsonl

LLM-as-judge calibration
Cohen's kappa 0.58 (moderate); reliable on summarization, factual_qa, math; not reliable on refusals

raw agreement: 80%  (95% CI 68% to 88%, n=60)
Cohen's kappa: 0.58  (moderate)

By category (weakest agreement first)
  kappa -0.33  acc  33%  n=12  refusals  [NOT reliable]
  kappa  0.66  acc  83%  n=12  summarization  [reliable]
  kappa  0.87  acc  94%  n=18  factual_qa  [reliable]
  kappa  0.89  acc  94%  n=18  math  [reliable]

Bias probe: position / order
  flip rate 33% (4/12 pairs changed pick when swapped); 4 favored the first-shown answer both times
Bias probe: verbosity
  length vs pass correlation r=0.04  (mean length passed 61 chars, failed 56 chars)

Verdict (kappa threshold 0.60, minimum 8 items per category)
  RELIABLE, safe to deploy as an auto-grader here:
    ...
  NOT RELIABLE, do not deploy without a human in the loop:
    refusals: kappa -0.33 (worse than chance), n=12 [kappa below threshold]
```

That is a real run against the bundled set. The 80 percent agreement looks deployable. The per-category kappa says do not deploy this judge on refusals, where it is worse than a coin flip. One number hides that. The calibration surfaces it.

## Quickstart (30 seconds)

```bash
git clone https://github.com/bengodgart/llm-judge-calibration
cd llm-judge-calibration
python -m judgecal calibrate --labeled data/labeled_sample.jsonl --pairwise data/pairwise_sample.jsonl
```

Python 3.9+, standard library only, no install, no API key, no cost. Add `--html report.html --md report.md` to also write the report files. A committed sample report is in [examples/](examples/).

## What it measures

- **Raw agreement** between the judge and the human, with a 95 percent Wilson confidence interval so a small sample is not read as more precise than it is.
- **Cohen's kappa**, overall and per category. Kappa corrects for the agreement you would get by chance, which is why a judge can hit 33 percent raw agreement on refusals and still score below zero: it is not just missing, it is anti-correlated with the human.
- **Per-category confusion** so you can see where the judge and human disagree most.
- **Position or order bias.** For pairwise comparisons, show the judge the two answers in both orders. If its pick changes when you swap them, that is order sensitivity, not judgment. The bundled pairwise set flips on 4 of 12 pairs, every one favoring the first-shown answer.
- **Verbosity bias.** Correlation between output length and a pass verdict. On the bundled set this is near zero (r = 0.04), so this particular judge does not reward length. Reporting the null is part of the point: not every bias is present, and you should measure rather than assume.

## The verdict block

A category is called reliable when Cohen's kappa is at least the threshold (0.60 by default, tunable with `--kappa-threshold`) and it has at least `--min-category-n` items (8 by default), so a handful of lucky agreements never earns a "reliable" stamp. Everything else is flagged not reliable, with the reason shown. On the bundled set:

- **Reliable:** factual_qa (kappa 0.87), math (kappa 0.89), summarization (kappa 0.66).
- **Not reliable:** refusals (kappa -0.33, worse than chance).

## Scoring your own judge

Produce a JSONL where each line is one graded output:

```json
{"id": "r1", "category": "refusals", "input": "...", "output": "...", "human_label": "pass", "judge_label": "fail", "judge_rationale": "..."}
```

`human_label` and `judge_label` are the two verdicts to compare (any label set, not just pass/fail). `category` drives the breakdown. Then:

```bash
python -m judgecal calibrate --labeled your_data.jsonl --html report.html
```

Add `--min-kappa 0.6` to exit non-zero when overall kappa falls below a gate, so a rubric change that quietly degrades agreement can fail a build.

### The pairwise file (optional)

The position probe needs its own file, one A/B comparison per line:

```json
{"id": "p1", "input": "...", "answer_a": "...", "answer_b": "...", "pick_original": "a", "pick_swapped": "b"}
```

`pick_original` is what the judge chose shown order [a, b]; `pick_swapped` is what it chose after swapping to [b, a]. Each names the stable content ("a" or "b"), so a differing pick is a position flip.

## Re-running the judge live (optional, off by default, costs money)

Everything above scores a judge's already recorded verdicts, so it runs offline at zero cost and calls no API. If you have rows with no `judge_label` and want to fill them in, `--run-judge` will call a judge model with your own key:

```bash
export ANTHROPIC_API_KEY=sk-...
python -m judgecal calibrate --labeled your_data.jsonl --run-judge --rubric your_rubric.txt --model claude-3-5-haiku-latest
```

This is the only path in the tool that touches the network. It is off by default, uses your key, and is not exercised by the offline tests. The calibration, which is the point, needs none of it.

## The bundled sample set

60 graded outputs across four categories (factual QA, math, summarization, refusals), each with a human label, the judge's label, and the judge's rationale, plus 12 pairwise comparisons for the position probe. It is designed so the judge is genuinely reliable on two categories and genuinely broken on one, so the verdict block has something honest to say. Full provenance and construction notes are in [data/DATASHEET.md](data/DATASHEET.md).

- Data license: CC BY 4.0.
- Code license: MIT.

## Tests

```bash
python -m pytest -q   # 21 tests, no third-party runtime deps
```

The tests pin the headline numbers (kappa 0.58, 80 percent agreement, the -0.33 refusals kappa, the 4/12 flip rate) against hand-worked values, so a change that moves the math trips a test.

## Why I built it

The evals hiring guides are explicit that the rare, hire-worthy skill is the judgment to know when an LLM-as-judge is reliable enough to deploy and when it is not, and that the judge-versus-human calibration writeup is the single rarest high-signal artifact, the one screeners probe for and almost no portfolio has. I use LLM-as-judge like everyone else, so I built the thing that checks it, and published a run where the honest answer is "not on refusals."

## License

Code MIT, data CC BY 4.0. See [LICENSE](LICENSE) and [data/DATASHEET.md](data/DATASHEET.md).
