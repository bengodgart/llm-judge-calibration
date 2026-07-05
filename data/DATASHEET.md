# Datasheet: LLM-as-judge calibration sample set (v0.1.0)

A datasheet in the spirit of Gebru et al., "Datasheets for Datasets."

## Motivation

Calibrating an LLM-as-judge against human labels needs a labeled set that has both a human verdict and the judge's verdict on the same outputs. Real ones are private. This is a small, open, documented sample set so a stranger can run a full calibration report in seconds with no data of their own, and so the tool's behavior can be demonstrated on a case where the honest answer is "the judge is not reliable here."

## Composition

- **60 graded outputs** across four categories: factual QA (18), math (18), summarization (12), refusals (12).
- Each row carries: `id`, `category`, `input` (the task shown), `output` (the assistant answer being graded), `human_label` (the reference verdict, pass or fail), `judge_label` (the LLM judge's verdict), and `judge_rationale` (the judge's one-line reason).
- A separate **12-row pairwise set** (`pairwise_sample.jsonl`) for the position probe: `id`, `input`, `answer_a`, `answer_b`, `pick_original` (the judge's choice shown order [a, b]), `pick_swapped` (its choice after swapping to [b, a]).

### What the labels mean

The judge is a pointwise pass/fail grader: does this output correctly and safely answer the input? `human_label` is the correct verdict a careful person would give. `judge_label` is what a plausible but naive LLM judge produced. The gap between them is the whole subject of the tool.

## Collection process

**All items are original and synthetic.** They were written for this dataset to look like realistic graded outputs. No text was copied from any product's logs, any user's data, or any proprietary eval set. The labels were assigned by the author to make the categories behave in specific, documented ways so the calibration has something honest to report:

- **factual_qa and math** are categories where the judge is broadly reliable: it agrees with the human on all but one item each, giving a high kappa. These are the clear-cut cases LLM judges handle well.
- **summarization** is a middling category: the judge agrees on most items but splits on brevity and on a fluent-but-wrong summary, landing at a moderate-to-substantial kappa.
- **refusals** is the category where the judge is deliberately, systematically wrong, to model the real and documented failure: a naive "was it helpful and did it answer" judge penalizes correct, safe refusals (marks them fail because they did not answer) and rewards harmful compliance (marks it pass because it was fluent and complete). This produces agreement worse than chance (kappa -0.33) and is the point of the "not reliable on refusals" verdict.

The pairwise set includes 4 pairs (of 12) where the judge's pick flips when the two answers are swapped, each flip favoring the first-shown answer, to model position or order bias.

## Uses

- Demonstrate and smoke-test the calibration harness end to end.
- A template for building a real calibration set: replace the rows with your own graded outputs, keep the schema, and run the same report.
- A teaching example of why a single agreement number is misleading and why kappa can go negative.

**Not** a benchmark of any real model or judge, not a safety evaluation, and not a source of ground truth about how any specific production judge behaves. The labels are authored to exercise the tool, not measured from a live system.

## Limitations

- 60 items is small; per-category cells are 12 to 18 items, so category kappa is indicative, not definitive. The tool reports a confidence interval on accuracy precisely to keep this honest, and refuses to call a category reliable below a minimum item count.
- The labels are synthetic and author-assigned. They are designed to be realistic and internally consistent, not sampled from real annotators.
- Two label classes only (pass/fail). Ordinal or multi-class judges would want weighted kappa, noted in the parking lot.

## Distribution & license

- Data: CC BY 4.0.
- Code (the calibration harness): MIT.

## Maintenance

Versioned in the repository. Contributions of additional original, documented rows (with a human label, a judge label, and a category) are welcome via pull request.
