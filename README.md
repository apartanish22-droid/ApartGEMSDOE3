# ApartGEMSDOE3 — GEMS geothermal-fault discovery: research, submission, and release review

> **Standing project prompt (read at the start of every session).** Goal: place at the top of the DOE GEMS Prize leaderboard (https://www.drivendata.org/competitions/306/competition-doe-gems/) with a defensible, unique, high-scoring geothermal-fault propensity submission. Core values: **Maximize P(Win)** and **Own the Outcome**. No hallucinations; verify line by line from official/trusted sources; flag irregularities.

## Competition
- Overview: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Problem description: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Data (login-walled): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Organizer reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Submission format: single-band GeoTIFF (.tif) or .zip containing one GeoTIFF; must match the submission format's CRS, shape, and geotransform; values must be in [0, 1] (portal error: "Predicted values must be in range [0, 1]"). Note field (&le;140 chars, e.g. "clustering with k=25").
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Official sources: USGS GeoDAWN https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and · INGENIOUS https://gbcge.org/current-projects/ingenious/ · EPSG:32611 https://epsg.io/32611 · Tversky index https://en.wikipedia.org/wiki/Tversky_index · GDR 1391 https://gdr.openei.org/submissions/1391

## Focus sites (owner-reported scores, NOT organizer-confirmed)
GEMSDOE24 · GEMSDOE25 · GEMSDOE27 · GEMSDOE28 · GEMSDOE30 · GEMSDOE31 · GEMSDOE32 · GEMSDOE33 · GEMSDOE36. Best owner-reported among them: GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` = 0.2778. See `docs/executive-summary.html` for the full nine-site table (file to download · estimated score · unique?).

## Parallel-run protocol (binding)
1. **Lane:** one method lane per run. Stop if raster rank-correlation with any registry raster > 0.90, or > 70% of dots within 3 px of one registry raster's dots. Check before placement AND on final dots.
2. **Reuse, don't rebuild:** shared cached feature stack, `scripts/evaluate_holdout.py`, `scripts/submission_writer.py`. Hold out whole fault segments with a buffer; derive catalogue features only from visible faults; mask visible faults pixel-exactly; pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). Fix shared tools centrally; no private forks.
3. **Label every number** as HOLDOUT-DTI (evaluator version, withheld positives, 95% CI) or ORGANIZER-CONFIRMED (submission receipt). A projection is never a score.
4. **Leakage canary:** test each feature alone on holdout; AUC > 0.90 means leakage until proven otherwise.
5. **Run card:** one JSON card per experiment (hypothesis; mechanism; non-fault mimic; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output; submission name + note &le;140 chars; verdict promote/negative). Negative results are deliverables.
6. **Budget:** stop after 3 experiments or 2 hours. Do not consume a submission slot on an unvalidated idea.

## Current status (this branch: arena/61ccce6b-apartgemsdoe3)
- **DO NOT SUBMIT &mdash; no submission is authorized.** The run-card verdict is negative; no weekly slot has been used.
- **Historical audit artifact (for audit/learning only, not for resubmission):** `apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif` &middot; SHA-256 `65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38` &middot; historical name `APARTGEMSDOE3-CSHD-37B32D5B`. Its former promotion is withdrawn; format-valid is not submit-ready.
- **Registry current research artifact** (per `registry/current_status.json`, also not OK to submit): candidate `H-APART3-2-CTHG-DHC`, artifact `apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif` &middot; SHA-256 `9d5cab2ed8b393cd509c196961481520772bee5b1791e322e0b15cdbba696112` &middot; name `APARTGEMSDOE3-CTHG-DHC-5D4D0085`; verdict negative (literal all-registry overlap >70%, band-6 total-count-as-tilt, no assigned lane, selector not run).
- A **unique TIF submission was generated** (this session): `docs/downloads/gemsdoe32-apart3-unique-offcatalogue-geophys-20261028T225009Z-22727d79-zeros.tif` (mirrored to `submission/`). It is **format-valid** (all 13 format/range checks pass: [0,1], no NaN, CRS/shape/transform match) but **NOT OK to submit to the leaderboard** &mdash; no DrivenData auth, no organizer receipt, holdout-DTI is a proxy not a live score, and it does not beat the incumbent catalogue holdout (~0.0992) so it is a negative verdict for slot use.
- It is **unique by construction**: label-free geophysical anomalies (radiometric total-count depletion, magnetic- and gravity-anomaly magnitude), every dot excluded from the USGS/INGENIOUS catalogue plus a 200 m collar; not a copy of any GEMSDOE24/25/27/28/30/31/32/33/36 reference raster.
- Download page: `index.html` (obvious "Download submission TIF" CTA). Detailed table: `docs/executive-summary.html`.

## Reproduce checks
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Restore pinned owner-mirror format inputs (NOT organizer-authenticated) into .cache/gems_data/
.venv/bin/python scripts/restore_data.py --group core
# Validate the generated submission
.venv/bin/python scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite docs/downloads/gemsdoe32-apart3-unique-offcatalogue-geophys-20261028T225009Z-22727d79-zeros.tif
# Release state
.venv/bin/python scripts/check_release_status.py
.venv/bin/python -m pytest -q
```

## Repository contents
- `docs/` — GitHub Pages research portal (executive summary, hypotheses, leaderboard, review, sources).
- `docs/downloads/` — hash-verified downloadable submission GeoTIFFs + audit sidecars.
- `submission/` — mirrors of submission-ready TIFs.
- `scripts/` — `build_unique_submission.py`, `submission_writer.py`, `check_submission.py`, `evaluate_holdout.py`, `restore_data.py`, `download_competition_data.sh`, `check_release_status.py`, `audit_nine_site_best.py`.
- `src/gems32/` — shared pipeline (metric, holdout, emission, submission).
- `evidence/` — run cards, audit receipts, run-card JSONs.
- `registry/` — manifests, slot plan, sources, current status, irregularities.

## Limitations
- No DrivenData authentication → cannot auto-download organizer-authenticated `training_features.tif`, `labels.tif`, `sample_submission.tif` from the competition data page (verified redirect to login). Owner-supplied mirrors are used for CI format checks only; they are integrity-pinned, NOT organizer-authenticated.
- The cached feature stack / full registry raster set are not present in this checkout; holdout-DTI is a spatial proxy, not a leaderboard-score conversion.
- Competing prompt leaderboard claims are not independently confirmed.
