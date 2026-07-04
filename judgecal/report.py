"""Render a Calibration to text, Markdown, or self-contained dark HTML."""

from __future__ import annotations

import html

from .calibrate import Calibration, CategoryResult


def _pct(x: float) -> str:
    return f"{x*100:.0f}%"


def _headline(cal: Calibration) -> str:
    reliable = ", ".join(c.name for c in cal.reliable_categories) or "none"
    unreliable = ", ".join(c.name for c in cal.unreliable_categories) or "none"
    return (
        f"Cohen's kappa {cal.kappa:.2f} ({cal.band}); "
        f"reliable on {reliable}; not reliable on {unreliable}"
    )


def _verdict_lines(cal: Calibration) -> list[str]:
    out: list[str] = []
    out.append(
        f"Verdict (kappa threshold {cal.kappa_threshold:.2f}, "
        f"minimum {cal.min_category_n} items per category)"
    )
    rel = cal.reliable_categories
    unrel = cal.unreliable_categories
    if rel:
        out.append("  RELIABLE, safe to deploy as an auto-grader here:")
        for c in rel:
            out.append(f"    {c.name}: kappa {c.kappa:.2f} ({c.band}), n={c.n}")
    if unrel:
        out.append("  NOT RELIABLE, do not deploy without a human in the loop:")
        for c in unrel:
            reason = "kappa below threshold" if c.n >= cal.min_category_n else "too few items"
            out.append(f"    {c.name}: kappa {c.kappa:.2f} ({c.band}), n={c.n} [{reason}]")
    return out


def render_text(cal: Calibration) -> str:
    lines: list[str] = []
    lines.append("LLM-as-judge calibration")
    lines.append(_headline(cal))
    lines.append("")
    ci = cal.accuracy_ci
    lines.append(
        f"raw agreement: {_pct(cal.accuracy)}  "
        f"(95% CI {_pct(ci.low)} to {_pct(ci.high)}, n={cal.n})"
    )
    lines.append(f"Cohen's kappa: {cal.kappa:.2f}  ({cal.band})")
    if cal.pending:
        lines.append(f"pending rows (no judge_label, not scored): {cal.pending}")
    lines.append("")
    lines.append("By category (weakest agreement first)")
    for c in cal.categories:
        flag = "reliable" if c.reliable else "NOT reliable"
        lines.append(
            f"  kappa {c.kappa:>5.2f}  acc {_pct(c.accuracy):>4}  n={c.n:>2}  "
            f"{c.name}  [{flag}]"
        )
    lines.append("")
    if cal.position is not None:
        p = cal.position
        lines.append("Bias probe: position / order")
        lines.append(
            f"  flip rate {_pct(p.flip_rate)} ({p.flips}/{p.n} pairs changed pick when swapped); "
            f"{p.first_position_wins} favored the first-shown answer both times"
        )
    v = cal.verbosity
    lines.append("Bias probe: verbosity")
    lines.append(
        f"  length vs pass correlation r={v.correlation:.2f}  "
        f"(mean length passed {v.mean_len_pass:.0f} chars, failed {v.mean_len_fail:.0f} chars)"
    )
    lines.append("")
    lines.extend(_verdict_lines(cal))
    return "\n".join(lines)


def _md_confusion(c: CategoryResult, labels: list[str]) -> list[str]:
    md: list[str] = []
    header = "| human \\ judge | " + " | ".join(labels) + " |"
    sep = "|---" * (len(labels) + 1) + "|"
    md.append(header)
    md.append(sep)
    for h in labels:
        cells = " | ".join(str(c.confusion.get((h, j), 0)) for j in labels)
        md.append(f"| **{h}** | {cells} |")
    return md


def render_markdown(cal: Calibration) -> str:
    md: list[str] = []
    md.append("# LLM-as-judge calibration report")
    md.append("")
    md.append(f"**{_headline(cal)}**")
    md.append("")
    ci = cal.accuracy_ci
    md.append(
        f"- **Raw agreement:** {_pct(cal.accuracy)} "
        f"(95% CI {_pct(ci.low)} to {_pct(ci.high)}, n={cal.n})"
    )
    md.append(f"- **Cohen's kappa:** {cal.kappa:.2f} ({cal.band})")
    if cal.pending:
        md.append(f"- Pending rows (no judge_label, not scored): {cal.pending}")
    md.append("")
    md.append("## By category (weakest agreement first)")
    md.append("")
    md.append("| Category | Kappa | Band | Agreement | n | Reliable |")
    md.append("|---|---|---|---|---|---|")
    for c in cal.categories:
        md.append(
            f"| {c.name} | {c.kappa:.2f} | {c.band} | {_pct(c.accuracy)} | {c.n} | "
            f"{'yes' if c.reliable else 'no'} |"
        )
    md.append("")
    md.append("## Verdict")
    md.append("")
    md.append(
        f"Threshold: a category is called reliable when Cohen's kappa is at least "
        f"{cal.kappa_threshold:.2f} and it has at least {cal.min_category_n} items."
    )
    md.append("")
    if cal.reliable_categories:
        md.append("**Reliable, safe to deploy as an auto-grader:**")
        for c in cal.reliable_categories:
            md.append(f"- {c.name}: kappa {c.kappa:.2f} ({c.band}), n={c.n}")
        md.append("")
    if cal.unreliable_categories:
        md.append("**Not reliable, keep a human in the loop:**")
        for c in cal.unreliable_categories:
            reason = "kappa below threshold" if c.n >= cal.min_category_n else "too few items"
            md.append(f"- {c.name}: kappa {c.kappa:.2f} ({c.band}), n={c.n} ({reason})")
        md.append("")
    md.append("## Bias probes")
    md.append("")
    if cal.position is not None:
        p = cal.position
        md.append(
            f"- **Position / order bias:** flip rate {_pct(p.flip_rate)} "
            f"({p.flips} of {p.n} pairs changed pick when the two answers were swapped). "
            f"{p.first_position_wins} of those favored the first-shown answer both times."
        )
    v = cal.verbosity
    md.append(
        f"- **Verbosity bias:** correlation between output length and a pass verdict "
        f"r={v.correlation:.2f}. Mean length of passed outputs {v.mean_len_pass:.0f} chars, "
        f"failed {v.mean_len_fail:.0f} chars."
    )
    md.append("")
    md.append("## Per-category confusion")
    md.append("")
    for c in cal.categories:
        md.append(f"### {c.name} (n={c.n})")
        md.append("")
        md.extend(_md_confusion(c, cal.labels))
        md.append("")
    if cal.disagreements:
        md.append("## Where the judge and the human disagree")
        md.append("")
        md.append("| id | category | human | judge | judge rationale |")
        md.append("|---|---|---|---|---|")
        for d in cal.disagreements:
            rat = d.judge_rationale.replace("|", "/")
            md.append(
                f"| {d.id} | {d.category} | {d.human_label} | {d.judge_label} | {rat} |"
            )
        md.append("")
    return "\n".join(md)


def _bar(value: float, low: float, high: float) -> str:
    # map a kappa in [-0.4, 1.0] to a 0..100 bar
    span_lo, span_hi = -0.4, 1.0
    frac = (value - span_lo) / (span_hi - span_lo)
    frac = max(0.0, min(1.0, frac))
    color = "#22c55e" if value >= high else ("#f59e0b" if value >= 0.2 else "#ef4444")
    return (
        f"<div class='bar'><div class='fill' style='width:{frac*100:.0f}%;"
        f"background:{color}'></div></div>"
    )


def render_html(cal: Calibration) -> str:
    ci = cal.accuracy_ci
    thr = cal.kappa_threshold

    cat_rows = ""
    for c in cal.categories:
        flag = (
            "<span class='ok'>reliable</span>"
            if c.reliable
            else "<span class='bad'>not reliable</span>"
        )
        cat_rows += (
            f"<tr><td>{html.escape(c.name)}</td>"
            f"<td class='barcell'>{_bar(c.kappa, thr, thr)}"
            f"<span class='pct'>{c.kappa:.2f}</span></td>"
            f"<td>{html.escape(c.band)}</td>"
            f"<td class='num'>{_pct(c.accuracy)}</td>"
            f"<td class='num'>{c.n}</td><td>{flag}</td></tr>"
        )

    rel = "".join(
        f"<li><b>{html.escape(c.name)}</b>: kappa {c.kappa:.2f} ({html.escape(c.band)}), n={c.n}</li>"
        for c in cal.reliable_categories
    )
    unrel = "".join(
        f"<li><b>{html.escape(c.name)}</b>: kappa {c.kappa:.2f} ({html.escape(c.band)}), n={c.n}</li>"
        for c in cal.unreliable_categories
    )

    pos_html = ""
    if cal.position is not None:
        p = cal.position
        pos_html = (
            f"<div class='probe'><div class='lbl'>Position / order bias</div>"
            f"<div class='pv'>{_pct(p.flip_rate)} flip rate</div>"
            f"<div class='pe'>{p.flips} of {p.n} pairs changed the judge's pick when the two "
            f"answers were swapped. {p.first_position_wins} favored the first-shown answer both "
            f"times, the signature of pure order bias.</div></div>"
        )
    v = cal.verbosity
    verb_html = (
        f"<div class='probe'><div class='lbl'>Verbosity bias</div>"
        f"<div class='pv'>r = {v.correlation:.2f}</div>"
        f"<div class='pe'>Correlation between output length and a pass verdict. Passed outputs "
        f"averaged {v.mean_len_pass:.0f} characters, failed {v.mean_len_fail:.0f}. A positive "
        f"number means the judge leans toward longer answers.</div></div>"
    )

    dis_rows = ""
    for d in cal.disagreements:
        dis_rows += (
            f"<tr><td>{html.escape(d.id)}</td><td>{html.escape(d.category)}</td>"
            f"<td class='hl'>{html.escape(d.human_label)}</td>"
            f"<td class='jl'>{html.escape(d.judge_label)}</td>"
            f"<td>{html.escape(d.judge_rationale)}</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM-as-judge calibration report</title>
<style>
  body{{margin:0;background:#0f172a;color:#e2e8f0;font-family:-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6;}}
  .wrap{{max-width:820px;margin:0 auto;padding:32px 20px 64px;}}
  h1{{font-size:1.6rem;margin:0 0 4px;}}
  h2{{font-size:1.15rem;border-bottom:1px solid #334155;padding-bottom:.3em;margin:1.8em 0 .6em;color:#fff;}}
  .big{{font-size:2rem;font-weight:700;color:#38bdf8;}}
  .sub{{color:#94a3b8;font-size:.9rem;}}
  .headline{{background:#1e293b;border:1px solid #334155;border-left:4px solid #38bdf8;border-radius:10px;padding:14px 18px;margin:16px 0;}}
  table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:.9rem;}}
  th{{text-align:left;color:#94a3b8;font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;border-bottom:1px solid #334155;padding:6px 10px;}}
  td{{padding:7px 10px;border-bottom:1px solid #334155;vertical-align:middle;}}
  td.num{{text-align:right;color:#cbd5e1;font-variant-numeric:tabular-nums;white-space:nowrap;}}
  .barcell{{width:34%;}}
  .bar{{display:inline-block;width:calc(100% - 46px);height:12px;background:#243349;border-radius:6px;overflow:hidden;vertical-align:middle;}}
  .fill{{height:100%;}}
  .pct{{margin-left:8px;color:#cbd5e1;font-size:.82rem;font-variant-numeric:tabular-nums;}}
  .ok{{color:#22c55e;font-weight:600;}}
  .bad{{color:#ef4444;font-weight:600;}}
  .verdict{{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0;}}
  .card{{flex:1;min-width:240px;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px 16px;}}
  .card.good{{border-left:4px solid #22c55e;}}
  .card.warn{{border-left:4px solid #ef4444;}}
  .card h3{{margin:0 0 6px;font-size:1rem;color:#fff;}}
  .card ul{{margin:0;padding-left:18px;font-size:.9rem;}}
  .probes{{display:flex;gap:14px;flex-wrap:wrap;}}
  .probe{{flex:1;min-width:240px;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px 16px;}}
  .probe .lbl{{color:#94a3b8;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;}}
  .probe .pv{{font-size:1.5rem;font-weight:700;color:#f59e0b;margin:2px 0;}}
  .probe .pe{{color:#94a3b8;font-size:.85rem;}}
  td.hl{{color:#22c55e;font-weight:600;}}
  td.jl{{color:#ef4444;font-weight:600;}}
</style></head><body><div class="wrap">
<h1>LLM-as-judge calibration report</h1>
<div class="headline">{html.escape(_headline(cal))}</div>
<p><span class="big">{_pct(cal.accuracy)}</span> <span class="sub">raw agreement
  (95% CI {_pct(ci.low)} to {_pct(ci.high)}, n={cal.n}) &middot;
  Cohen's kappa <b>{cal.kappa:.2f}</b> ({html.escape(cal.band)})</span></p>

<h2>By category</h2>
<table><tr><th>Category</th><th>Kappa</th><th>Band</th><th>Agreement</th><th>n</th><th>Verdict</th></tr>
{cat_rows}</table>

<h2>Verdict</h2>
<p class="sub">A category is called reliable when Cohen's kappa is at least {thr:.2f}
  and it has at least {cal.min_category_n} items.</p>
<div class="verdict">
  <div class="card good"><h3>Reliable, deploy as an auto-grader</h3><ul>{rel or "<li>none</li>"}</ul></div>
  <div class="card warn"><h3>Not reliable, keep a human in the loop</h3><ul>{unrel or "<li>none</li>"}</ul></div>
</div>

<h2>Bias probes</h2>
<div class="probes">{pos_html}{verb_html}</div>

<h2>Where the judge and the human disagree</h2>
<table><tr><th>id</th><th>category</th><th>human</th><th>judge</th><th>judge rationale</th></tr>
{dis_rows}</table>

<p class="sub" style="margin-top:24px">Deterministic scoring of pre-recorded judge verdicts against human
  labels. No API is called on this path. Kappa, the Wilson confidence interval, and the correlations
  are computed on the standard library. Generated by judgecal.</p>
</div></body></html>"""
