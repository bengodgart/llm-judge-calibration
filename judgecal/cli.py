"""Command-line interface for judgecal.

Usage:
    python -m judgecal calibrate --labeled data/labeled_sample.jsonl \\
        [--pairwise data/pairwise_sample.jsonl] [options]

The labeled file is JSONL, one graded output per line:
    {"id", "category", "input", "output", "human_label", "judge_label",
     "judge_rationale"}
It scores the already recorded judge_label against the human_label. No API is
called on this path, so it runs offline at zero cost.

Options:
    --pairwise PATH       also run the position-swap probe on a pairwise file
    --html PATH           also write an HTML report
    --md PATH             also write a Markdown report
    --kappa-threshold F   kappa at or above F counts as reliable (default 0.6)
    --min-category-n N    a category needs at least N items to be called
                          reliable (default 8)
    --min-kappa F         exit non-zero if overall kappa is below F; off by default
    --run-judge           re-run the judge live on rows missing a judge_label,
                          using your own API key (see judgecal.judge). Off by
                          default. This is the only path that calls an API.
    --rubric PATH         rubric prompt file for --run-judge
    --model NAME          judge model for --run-judge
    --quiet               suppress the text report on stdout

Exit code 0 normally (or if kappa meets --min-kappa), 1 if below the gate,
2 on a usage or IO error.
"""

from __future__ import annotations

import argparse
import os
import sys

from .calibrate import calibrate
from .dataset import load_labeled, load_pairwise
from . import report as report_mod


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="judgecal",
        description="Calibrate an LLM-as-judge against human labels: agreement, bias, verdict.",
    )
    sub = parser.add_subparsers(dest="command")
    c = sub.add_parser("calibrate", help="score a judge's recorded verdicts against human labels")
    c.add_argument("--labeled", required=True)
    c.add_argument("--pairwise", default=None)
    c.add_argument("--html", default=None)
    c.add_argument("--md", default=None)
    c.add_argument("--kappa-threshold", type=float, default=0.6, dest="kappa_threshold")
    c.add_argument("--min-category-n", type=int, default=8, dest="min_category_n")
    c.add_argument("--min-kappa", type=float, default=None, dest="min_kappa")
    c.add_argument("--positive-label", default="pass", dest="positive_label")
    c.add_argument("--run-judge", action="store_true", dest="run_judge")
    c.add_argument("--rubric", default=None)
    c.add_argument("--model", default=None)
    c.add_argument("--quiet", action="store_true")
    return parser


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def run(args) -> int:
    try:
        rows = load_labeled(args.labeled)
        pairwise = load_pairwise(args.pairwise) if args.pairwise else None
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc.filename}", file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.run_judge:
        # The single optional path that calls an API. Imported lazily so the
        # offline default never touches the network code.
        try:
            from .judge import run_judge
            run_judge(rows, rubric_path=args.rubric, model=args.model)
        except Exception as exc:                          # noqa: BLE001 - surface any live-run error plainly
            print(f"error: --run-judge failed: {exc}", file=sys.stderr)
            return 2

    cal = calibrate(
        rows,
        pairwise=pairwise,
        kappa_threshold=args.kappa_threshold,
        min_category_n=args.min_category_n,
        positive_label=args.positive_label,
    )

    if not args.quiet:
        print(report_mod.render_text(cal))
    if args.html:
        _ensure_parent(args.html)
        with open(args.html, "w", encoding="utf-8") as handle:
            handle.write(report_mod.render_html(cal))
        if not args.quiet:
            print(f"\nwrote HTML report: {args.html}")
    if args.md:
        _ensure_parent(args.md)
        with open(args.md, "w", encoding="utf-8") as handle:
            handle.write(report_mod.render_markdown(cal))
        if not args.quiet:
            print(f"wrote Markdown report: {args.md}")

    if args.min_kappa is not None and cal.kappa < args.min_kappa:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "calibrate":
        return run(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
