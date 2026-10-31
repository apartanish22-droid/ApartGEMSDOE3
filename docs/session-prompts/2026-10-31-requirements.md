# Session requirements — 2026-10-31 (condensed record)

**What this file is.** A dated, condensed record of the requirements in the 2026-10-31 session prompt, so every session starts from the same brief. The original prompt repeats several blocks (the "Work line by line…" paragraph, the "no hallucinations" paragraph, and the parallel-run protocol) many times. This file keeps each requirement once. It does not reproduce every duplicate.

**Read this before every session.** The README links here. Re-read the official pages before quoting any number.

## 1. Goal

- Place at the top of the DrivenData leaderboard: [competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- Produce a **unique** GeoTIFF submission that is downloadable from the site. It must be obvious whether it is OK to download and submit.
- No human inspection. Validation must be automated through the project.

## 2. Submission rules (checked against the official page, fetched 2026-10-31)

- Single-band float32 GeoTIFF, EPSG:32611, 100 m, same bounds as `training_features.tif`, values between 0 and 1, "data outside the bounds is null or nan" (official wording).
- Portal error seen by the owner: "Predicted values must be in range [0, 1]". The repo's strict check requires whole-array finiteness with values in [0, 1]. Zeros outside the footprint satisfy both rules.
- Name (unique) and note (≤ 140 characters).
- Choose a single submission across both prize rounds.

## 3. Method rules (repo protocol)

1. **Lane.** Each run must have an assigned method lane. No lane is assigned in this checkout. Runs are labelled "self-declared" and cannot be cleared for a weekly slot until an owner assigns one.
2. **Uniqueness.** Compare the surface before placement and the final dots against every registry raster. Duplicate if |Spearman| > 0.90 or more than 70 % of dots lie within 3 px of one registry raster.
3. **Shared tools only.** `scripts/evaluate_holdout.py`, `scripts/submission_writer.py`, `src/gems32/holdout.py`. Fix defects centrally.
4. **Holdout.** Hide-and-recover with whole fault segments and a buffer; catalogue features only from visible faults; pooled DTI with α = 0.2, β = 0.8 and a 300 m triangular kernel.
5. **Leakage canary.** Test each feature alone on the holdout. AUC above 0.90 is leakage until proven otherwise.
6. **Labels.** Every number is HOLDOUT-DTI (evaluator version, withheld positives, 95 % CI), ORGANIZER-CONFIRMED (copied from a submission-page receipt) or OWNER-REPORT. A projection is never written as a score.
7. **Run card.** Each experiment ends with a JSON card: hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, correlation/overlap versus registry, raster SHA-256, validator output, submission name and note, verdict (promote or negative).
8. **Budget.** Stop after 3 experiments or 2 hours. A positive result is not a slot authorization.

## 4. Candidate generation

- Generate 3–5 hypotheses before implementing. Name the layers, the physical signature, why it should catch an off-catalogue fault, the named non-fault mimic, and the overlap with existing code. Rank by expected improvement and cost. See `docs/research/h-candidates-20261031.md`.
- Validate the top candidate on the holdout before touching a submission slot.

## 5. Research and provenance

- Use official, verified sources, with links for manual review. Flag irregularities. Do not hallucinate. Verify line by line.
- Known irregularities: the prompts cite leaderboard values of 0.4413 and 0.3195; the public page read on 2026-10-31 shows #1 at 0.4544. Treat the prompt values as unverified.
- Store research knowledge in the repo so it can serve other projects.

## 6. Working agreement

- Core values: **Maximize P(Win)** and **Own the Outcome**.
- Multi-pass work: implement, review for bugs and missing requirements, then re-check against the original request.
- Work on branch `arena/f9804780-apartgemsdoe3` and open PRs from it.

## 7. Limits

- DrivenData, Dropbox, GDR and USGS are not reachable from the sandbox. The official problem and leaderboard pages were read through the fetch tool.
- Training inputs are restored from pinned owner mirrors on GitHub, SHA-256 verified. They are **not organizer-authenticated**.
