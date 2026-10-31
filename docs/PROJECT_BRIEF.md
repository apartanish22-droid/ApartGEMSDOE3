# Project brief — read at the start of every session

> **Condensed from the session brief of 2026-10-31.** The original message repeated the same
> requirements many times; each distinct requirement is kept here once. Nothing is added.
> The brief is the starting point for every session. Re-read it before doing any work.

## Goal

Place at the top of the DrivenData **GEMS (DOE) geothermal fault-discovery competition** leaderboard by
producing a single-band GeoTIFF of predicted geothermal-fault probabilities that the portal accepts.

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Problem description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Data (login required): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Submission format spec (NLR): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution

## Non-negotiable requirements

1. **A submission must be a real, unique GeoTIFF that passes the portal format.** A `.tif` (or a `.zip`
   containing one) with the template's CRS, shape, and geotransform, and predicted values in **[0, 1]**.
   The portal error *"Predicted values must be in range [0, 1]"* must not occur.
2. **Every submission gets a unique name and a short note (≤140 characters)** so it can be told apart later.
3. **Unique.** Not a duplicate of any prior submission, including the GEMSDOE sites listed in the session brief.
   Copies are permitted only for learning and education, never for submitting.
4. **The download link must be obvious** on the first screen of the site, with the file, its estimated score,
   and whether it is unique. Estimated score and uniqueness go in an executive-summary table.
5. **Validation is automated.** Gates run in code (format, leakage canaries, holdout, uniqueness, selector cap).
   No human inspection is part of validation.
6. **Labels on every number:** `HOLDOUT-DTI` (evaluator version, withheld positives, 95% CI),
   `ORGANIZER-CONFIRMED` (copied from a submission-page receipt), or `OWNER-REPORT` / `PUBLIC-LEADERBOARD-OBSERVATION`.
   A projection is never written as a score.
7. **Leakage canary:** every single feature is tested alone on the holdout. AUC > 0.90 means leakage until proven otherwise.
8. **Run card** per experiment: hypothesis, mechanism, named non-fault mimic, holdout DTI + CI,
   correlation/overlap vs registry, raster SHA-256, validator output, submission name + note, verdict
   (`promote` or `negative`). Negative results are deliverables.
9. **Budget:** stop after 3 experiments or 2 hours per lane. A positive result is not authorization; the
   weekly-slot selector is a separate step.
10. **Verify everything line by line** against official, verified sources, with links for manual review.
    Flag irregularities. No hallucinated numbers, links, or claims.

## Scientific direction

- Hypotheses must name the layer(s), the physical signature, why it should catch a fault missing from
  the USGS/INGENIOUS catalogue, and how it differs from what is already in the repo.
- Rank candidates by expected DTI improvement and implementation cost. Validate the top candidate on the
  spatially blocked holdout before spending any submission slot.
- Look for under-used free official data (state geological surveys, USGS, NASA, EPSG resources). Confirm it is
  obtainable before proposing it. Record each source and its access status.
- Be contrarian but grounded in peer-reviewed or official methodology.

## Core values (keep as the focal point)

- **Maximize P(Win):** weigh tradeoffs and risk; choose the path that maximizes the probability of a
  high, legitimate leaderboard score.
- **Own the Outcome:** own results end to end; treat failure and success as signals; act when the means exist.

## Process rules

- Work in passes: implement, then review for bugs and missing requirements, then re-check against this brief.
- Work only on the branch assigned by Arena for the current session. Never switch, rename, or push to a different branch.
- Do not put credentials in the repo or in chat.
- Large data stays out of Git (see `.gitignore` and `scripts/restore_data.py`).

## Current status

See the [executive summary](executive-summary.html) for the current download/submit verdict and the
per-site table, and [repo review 2026-10-30](repo-review-2026-10-30.md) for the most recent verified review.
