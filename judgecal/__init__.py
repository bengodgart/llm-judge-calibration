"""judgecal: calibrate an LLM-as-judge against human labels.

Reads a labeled JSONL of {id, input, output, human_label, judge_label,
judge_rationale}, then reports how well the judge agrees with the human:
raw accuracy with a 95 percent confidence interval, Cohen's kappa overall and
per category, a per-category confusion breakdown, and two bias probes (position
or order bias via a swap flip rate, verbosity bias via a length correlation).

It ends with an honest verdict: the categories where the judge is reliable
enough to deploy and the ones where it is not, with the threshold visible.

Deterministic and offline. It scores a judge's already recorded verdicts, so
the default path calls no API and costs nothing. Re-running the judge live is an
optional path (judgecal.judge) that uses your own key and is off by default.
Stdlib only. See README.md.
"""

__version__ = "0.1.0"
