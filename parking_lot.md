# Parking lot — llm-judge-calibration

Ideas that surfaced during the v1 build. NOT in v1 scope.

- **Auto-suggest rubric edits** from the disagreement cases: cluster where the judge and human split and propose a rubric line that would fix it. Suggest-only, never auto-apply.
- **CI kappa gate** wired into a GitHub Action so a rubric change that drops agreement below a threshold fails the build (cross-links to the prompt-regression brief 03).
- **Judge leaderboard**: run several judge prompts on the same labeled set and rank them by kappa, to pick the best grader rather than the first one.
- **More agreement stats**: weighted kappa for ordinal label sets, Krippendorff's alpha for more than two raters, per-class precision and recall on the judge.
- **Bootstrap CI on kappa** itself, not just on accuracy, so the uncertainty on the headline number is visible too.
- **Richer position probe**: a separate first-position win rate and a tie-handling mode, beyond the single flip rate.

Product-creep tripwire (doctrine T11): a hosted dashboard with accounts, stored datasets, and a judge marketplace is an app. Stop and park.
