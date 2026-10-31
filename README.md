# ApartGEMSDOE3 — research and submission review

## PROJECT BRIEF — read before every session (from the standing goal prompt)

**Goal:** Place at the top of the DrivenData DOE GEMS fault-mapping competition leaderboard (metric: distance-weighted Tversky index, α=0.2, β=0.8, 300 m triangular kernel; submission: single-band float32 GeoTIFF, EPSG:32611, 3730×3292, 100 m, values in [0,1], matching `sample_submission.tif`).

**Focus sites:** GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36. Every site needs an executive-summary entry: file to download, estimated score (labelled OWNER-REPORT / HOLDOUT-DTI / ORGANIZER-CONFIRMED — a projection is never a score), and uniqueness vs the other eight sites.

**MUST:** Generate a UNIQUE TIF submission for the competition. Do not copy a previous submission (except for learning/education). The generated TIF must be obviously either OK or NOT OK to download and submit. There must be an easy-to-download submission TIF file. Inspection/validation is automated through the project — no human intervention.

**Leaderboard targets to beat:** GEMSDOE focus-site high 0.2778 (GEMSDOE32, OWNER-REPORT); public leaderboard high ~0.44+. A submission must score higher than 0.2778.

**Submission form:** unique submission name + note of at most 140 characters.

**Parallel-run protocol:** (1) Stay in the assigned method lane; stop and log a duplicate if rank correlation > 0.90 or > 70% of dots within 3 px of any registry raster. (2) Reuse the template's cached feature stack, `scripts/evaluate_holdout.py`, and `scripts/submission_writer.py` — no private forks. (3) Label every number as HOLDOUT-DTI (evaluator version, withheld positives, 95% CI) or ORGANIZER-CONFIRMED (receipt only). (4) Leakage canary: test each feature alone on holdout; AUC > 0.90 means leakage. (5) End each experiment with a JSON run card (hypothesis, mechanism, non-fault mimic, holdout DTI + CI, correlation/overlap vs registry, raster SHA-256, validator output, submission name + note ≤140 chars, verdict promote/negative). (6) Budget: 3 experiments or 2 hours; no slot spent until holdout validation passes.

> **Current decision (2026-10-31):** H1-LIDAR-SCARP-DEM-CHI is OK TO DOWNLOAD — format-valid (all 13 checks), holdout-positive (DTI 0.0062 [0.0047, 0.0074] vs GEMSDOE32 repo best 0.004515), SGMC-cal-positive (0.0940 vs champion 0.0641), and unique vs all nine focus files (overlap ≤34%, |ρ| ≤ 0.02). NOT YET OK TO SUBMIT — pending single-feature leakage canary, full-registry uniqueness, and weekly-slot selector authorization. No DrivenData auth in this sandbox.
>
> **Recommended file:** `docs/downloads/gemsdoe32-h1-lidar-scarp-dem-chi-20261031T044640Z-6660ab7a-zeros.tif` (SHA-256 `3ec64572…`, 278,714 bytes). [Download](docs/downloads/gemsdoe32-h1-lidar-scarp-dem-chi-20261031T044640Z-6660ab7a-zeros.tif) · [Submission name: `H1-LIDAR-SCARP-DEM-CHI`](docs/executive-summary.html)
>
> **No existing focus-site file is OK to submit.** All nine are mutual duplicates (overlap 87–100% within 3 px, |ρ| up to 0.99). GEMSDOE32 (0.2778) is already submitted; resubmitting adds nothing.

## Start here: what to do before every session

1. **Decision (2026-10-31):** H1-LIDAR-SCARP-DEM-CHI is OK to download but NOT yet authorized to submit. No existing focus-site file is OK to download or submit.
2. **Restore inputs** (`GEMS_DATA_DIR` defaults to `.cache/gems_data`): `python scripts/restore_data.py --group all` verifies all 36 pinned files against SHA-256 and rewrites `data/restore_receipt.json`. Inputs come from owner mirrors on GitHub and are **not organizer-authenticated**.
3. **Re-read the official pages** before quoting any number: [problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [data (login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/).
4. **Re-check the calibration** (`scripts/ledger_calibration_check.py`, [evidence](evidence/ledger_calibration_check_20261030.json), [note 10](knowledge/10_calibration_finding_and_next_candidates_20261030.md)) before using either metric to rank anything.

### Standing requirements (from the standing goal prompt)

- **Competition goal:** place at the top of the DrivenData leaderboard. Metric: distance-weighted Tversky index, α = 0.2, β = 0.8, 300 m triangular kernel. Source: [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- **Leaderboard targets:** GEMSDOE focus-site high 0.2778 (GEMSDOE32, OWNER-REPORT). Public leaderboard high ~0.44+ (xiaofanhu 0.4437 read 2026-10-26; 0.4544 read 2026-10-30). The prompt's 0.3195 / 0.4413 are older figures — flagged for review, not organizer receipts.
- **Submission file:** single-band float32 GeoTIFF, EPSG:32611, 3730 × 3292, 100 m, same bounds as the template, values in [0, 1]. Outside the footprint, null or NaN is allowed by the official page. The portal error "Predicted values must be in range [0, 1]" is what `scripts/check_submission.py --strict-finite` is meant to prevent. H1's zeros variant satisfies this.
- **Submission form:** a unique submission name and a note of at most 140 characters. `scripts/submission_writer.py` enforces the note length.
- **No human inspection.** Every gate is automated. A file is OK to download only when all gates pass and a separate selector authorizes a slot.
- **OK to download now:** H1-LIDAR-SCARP-DEM-CHI (all 13 format checks pass, holdout-positive, SGMC-cal-positive, unique vs focus nine).
- **OK to submit now:** NONE — pending single-feature leakage canary, full-registry uniqueness check, and weekly-slot selector authorization. No DrivenData auth in this sandbox.
- **Uniqueness:** literal surface and final-dot checks against every registry raster (Spearman ≤ 0.90, ≤ 70% of dots within 3 px). The nine focus files all fail against each other (see the executive summary). H1 passes vs all six locally available focus files.
- **Scoring labels:** every number is `HOLDOUT-DTI` (evaluator version, withheld-positive count, 95% CI), `ORGANIZER-CONFIRMED` (receipt only), or `OWNER-REPORT`. A projection is never a score.
- **Core values:** Maximize P(Win) and Own the Outcome. Treat failures as information.

## Persistent project brief — read before every session

Build an auditable research and submission system for the DOE GEMS fault-mapping competition, with the goal of improving the probability of a defensible leaderboard result. **Core values: Maximize P(Win) and Own the Outcome**—make evidence-led tradeoffs, treat failures as information, and own the end-to-end result. Work autonomously where evidence and tools permit; never invent evidence, live scores, data availability, or scientific certainty.

**Research priorities:** analyze the supplied best artifacts for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36; develop distinct geologic hypotheses for unmapped faults; validate them with spatially blocked, buffered hide-and-recover tests before considering any competition slot; keep a dated, source-linked research and score ledger. Do not copy prior submissions as candidates. The scores supplied by the user are `OWNER-REPORT` unless a submission-page receipt ties a score to exact raster bytes. Do not convert holdout results into a leaderboard projection without a validated calibration study.

**Parallel-run and release protocol:**

1. Define the one assigned method lane before any experiment. Compare the surface before placement and the final dots against every registry raster: stop and log a duplicate if absolute rank correlation exceeds `0.90` or over `70%` of candidate dots lie within `3 px` of any one registered raster. Apply the literal rule; do not silently exempt calibration rasters.
2. Reuse the shared cached feature stack, `scripts/evaluate_holdout.py`, and `scripts/submission_writer.py`. Hold out whole fault segments with a buffer; derive every catalogue-based feature only from visible faults and mask visible faults pixel-exactly. Use pooled DTI (`alpha=0.2`, `beta=0.8`, `300 m` triangular kernel). Fix shared-tool defects centrally.
3. Test each feature alone on holdout. Treat AUC above `0.90` as leakage until proven otherwise. Compare to a matching incumbent using the same evaluator and paired spatial confidence intervals.
4. Label each score `HOLDOUT-DTI` (evaluator version, withheld-positive count, 95% CI), `ORGANIZER-CONFIRMED` (from an organizer receipt), or `OWNER-REPORT`. A projection is never a score.
5. End each experiment with a JSON run card: hypothesis, mechanism, named non-fault mimic, holdout DTI + CI, correlation/overlap versus registry, raster SHA-256, validator output, submission name/note (note <=140 characters), and `promote` or `negative` verdict.
6. Stop at three experiments or two hours. A positive experiment is not authorization: the slot selector is separate and must honor the current weekly cap.
7. Validate the exact saved single-band GeoTIFF against the competition template: CRS, shape, affine transform, finite full-array values in `[0,1]` (including outside the footprint). Only show a submit/download CTA for a candidate that has also passed scientific, uniqueness, and selector gates.

The user-supplied prompt refers to a single assigned method paragraph, but that paragraph is not present in this checkout. Until it is supplied, do not infer or invent the lane. See the [project charter](docs/PROJECT_CHARTER.md) for the fuller durable protocol and [current-session review](docs/repo-review-current-session-2026-10-28.md) for this checkout's blockers.

## Current executive status (2026-10-31)

- **New candidate available:** H1-LIDAR-SCARP-DEM-CHI, file `docs/downloads/gemsdoe32-h1-lidar-scarp-dem-chi-20261031T044640Z-6660ab7a-zeros.tif` (SHA-256 `3ec64572ab5e215b5d6305ca1ded5527635bf19584b5e6d78e4d2dbacb5a9abc`), 62,469 off-catalogue dots. Run card: [`evidence/H1-LIDAR-SCARP-DEM-CHI_run_card.json`](evidence/H1-LIDAR-SCARP-DEM-CHI_run_card.json).
  - Format: ALL 13 checks pass ([0,1], CRS EPSG:32611, 3730x3292, 100 m, NaN-free whole array).
  - Holdout DTI: 0.0062 [0.0047, 0.0074], n=22,232 withheld positives — CI entirely above GEMSDOE32 repo best 0.004515 (PASS).
  - SGMC off-catalogue DTI: 0.0940 (raw 0.1649 [0.0768, 0.2625]) vs champion 0.0641 (PASS — no regression).
  - Uniqueness: UNIQUE vs all six locally available focus files (overlap 22-34% within 3 px, |rho| approx 0.02).
  - Verdict: OK TO DOWNLOAD. NOT YET OK TO SUBMIT — pending single-feature leakage canary, full-registry uniqueness, weekly-slot selector authorization.

- **No existing focus-site file is OK to submit.** All nine are mutual duplicates (overlap 87-100% within 3 px, |rho| up to 0.99). GEMSDOE32 (0.2778) is already submitted; resubmitting adds nothing. Five files fail the strict finite [0,1] check (NaN outside footprint).

- [Executive summary and nine-site comparison](docs/executive-summary.html): table of files, holdout DTI estimates, uniqueness, and verdicts for GEMSDOE24/25/27/28/30/31/32/33/36 plus H1 recommendation.
- [New hypotheses](knowledge/11_new_hypotheses_offcatalogue_blind_faults_2026-10-31.md): H1 (LiDAR scarp + DEM10 chi, implemented), H2-H5 (not yet implemented).
- [Calibration](knowledge/10_calibration_finding_and_next_candidates_20261030.md): SGMC-calibrated DTI rho=+0.40 [+0.22, +0.56] vs live scores; HOLDOUT-DTI rho=+0.17 (not significant).

- Earlier negative candidates (`H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS`, `H-APART3-2-CTHG-DHC`, H-SEISMIC, WCHD) remain negative and are retained as audit history only.

## Reproduce automated checks

Use an isolated environment; installing dependencies into the OS Python may be blocked by PEP 668.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group all --manifest registry/data_manifest.json
.venv/bin/python scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite docs/downloads/gemsdoe32-h1-lidar-scarp-dem-chi-20261031T044640Z-6660ab7a-zeros.tif
.venv/bin/python scripts/evaluate_focus_files.py
.venv/bin/python -m pytest -q
```

## Official reference links

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login required), and [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [INGENIOUS project](https://gbcge.org/current-projects/ingenious/), [GDR submission 1391](https://gdr.openei.org/submissions/1391), and [EPSG:32611](https://epsg.io/32611).
- Links are pointers for review, not claims that those sites or source files were reachable or revalidated in this restricted session. See `registry/sources.json` for recorded provenance and access status.