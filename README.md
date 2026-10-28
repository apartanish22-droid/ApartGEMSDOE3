# ApartGEMSDOE3 — auditable GEMS fault-propensity research

> ## Current decision: **DO NOT SUBMIT**
> No current candidate is both scientifically cleared and unique under the literal registry rule. The latest research GeoTIFF is downloadable for audit only; format validation is not authorization. No competition slot was used.

This README is the durable starting brief. At the start of every session read it, [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md), [`registry/current_status.json`](registry/current_status.json), and the latest candidate card, then reread the full current user prompt for any newly assigned lane or constraints. Current three-pass review: [`docs/repo-review-2026-10-28-session.md`](docs/repo-review-2026-10-28-session.md); independent concurrent review: [`docs/repo-review-session-2026-10-28.md`](docs/repo-review-session-2026-10-28.md). Executive summary: [`docs/executive-summary.html`](docs/executive-summary.html).

## Project objective and decision principles

Develop a scientifically defensible, reproducible workflow that detects likely unmapped faults relevant to geothermal exploration in the DOE GEMS study area, maximizes the chance of a valid competition result, and owns the outcome from source data to release decision. Treat failures as evidence. Never turn a local metric, a projection, or an owner-reported score into an organizer-confirmed leaderboard result.

A downloadable GeoTIFF is **OK to submit only if** it passes the strict format/range validator, the buffered spatial holdout and single-feature leakage canaries, both pre-placement and final-dot comparisons against the applicable full raster registry, scientific-integrity checks, and a separate weekly-slot selector. A file can be downloaded for research while still being explicitly **not authorized for upload**.

## Required run protocol

1. **Stay in the assigned method lane.** Compare the proposed surface before placement and final emitted dots after placement against every registry raster. Stop if absolute rank correlation exceeds `0.90` or more than `70%` of candidate dots fall within `3 px` of any registry raster. There are no density/lattice exemptions in the current protocol. The latest review records that this session's assigned method paragraph was missing.
2. **Reuse shared tools.** Use the cached feature stack, `scripts/evaluate_holdout.py`, and `scripts/submission_writer.py`. Hold out whole fault segments with a buffer; derive catalogue-based channels only from visible faults; mask visible faults pixel-exactly; score pooled DTI with alpha `0.2`, beta `0.8`, and the `300 m` triangular kernel. Fix a shared-tool defect centrally, never in a private fork.
3. **Test leakage.** Evaluate each feature alone on the spatially blocked holdout. AUC above `0.90` is presumed leakage until proven otherwise.
4. **Label every number.** Use `HOLDOUT-DTI` plus evaluator version, withheld-positive count, and 95% CI; or `ORGANIZER-CONFIRMED` only when copied from a submission-page receipt tied to that file. User/site-provided scores are `OWNER-REPORT`. A projection is never reported as a score.
5. **Write a run card.** Record hypothesis, mechanism, plausible non-fault mimic, holdout result and CI, registry correlation/overlap, GeoTIFF SHA-256, validator output, submission name and a note of at most 140 characters, and `promote` or `negative` verdict.
6. **Respect budget and selector separation.** Stop at 3 experiments or 2 hours, whichever comes first. Do not use a competition slot for an idea that has not beaten the comparable incumbent holdout. A positive experiment is not an upload authorization; slot selection is separate.
7. **Validate exact bytes.** A submission is a single-band GeoTIFF matching the sample template's CRS, shape and affine transform. Values must be finite and within `[0,1]` over the whole array, including outside the footprint. Re-open and validate the saved file.
8. **Research before implementation.** Propose 3–5 distinct geological hypotheses, name layers/signatures, explain why each targets unmapped rather than known faults, distinguish it from existing repo methods, rank expected value/cost, and identify any missing official data source. Do not run an experiment until the lane, budget and required inputs are established.

Full operating details and safety constraints: [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md).

## Focus-site comparison

The values below reproduce the scores and candidate names supplied in the project prompt and recorded in the focus-site audit. They are **OWNER-REPORT**, not verified submission receipts or current leaderboard estimates. They identify artifacts to study, not files to resubmit.

| Site | Highest listed submission | Reported DTI | Status |
|---|---|---:|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | OWNER-REPORT `0.2477` | Historical; do not resubmit |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | OWNER-REPORT `0.2600` | Historical; do not resubmit |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | OWNER-REPORT `0.2449` | Historical; do not resubmit |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | OWNER-REPORT `0.2710` | Historical; do not resubmit |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | OWNER-REPORT `0.2600` | Historical; do not resubmit |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | OWNER-REPORT `0.2708` | Historical; do not resubmit |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | OWNER-REPORT `0.2778` | Highest listed; historical; do not resubmit |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | OWNER-REPORT `0.2632` | Historical; do not resubmit |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | OWNER-REPORT `0.2750` | Historical; do not resubmit |

The highest result in this supplied nine-site list is GEMSDOE32's `0.2778` OWNER-REPORT. The supplied `0.3195` and `0.4413` leaderboard claims conflict and have not been verified as current or tied to these files. There is **no defensible live-score estimate** for a new candidate. See [`knowledge/03_why_02778_and_the_anatomy_of_the_family.md`](knowledge/03_why_02778_and_the_anatomy_of_the_family.md) and the byte-level audits under `evidence/`.

## Latest artifact and release status

- Candidate: `H-APART3-2-CTHG-DHC`; audit submission name `APARTGEMSDOE3-CTHG-DHC-5D4D0085`; card: [`evidence/apart3_cthg_dhc_run_card.json`](evidence/apart3_cthg_dhc_run_card.json).
- Recorded note (metadata only; not authorization): `ApartGEMSDOE3 H-APART3-2 CTHG-DHC 37654d B2 d3.24 | HR=0.0997 Det=0.0960 SGMC=0.0824`.
- Research-only GeoTIFF: [`apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif`](docs/downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif).
- SHA-256: `9d5cab2ed8b393cd509c196961481520772bee5b1791e322e0b15cdbba696112`.
- Local `HOLDOUT-DTI`, `GEMSDOE32-HIDE-RECOVER-v3.0`, `n=22,232` withheld positives, 95% CI: `0.099651 [0.087243, 0.111947]`. This does **not** establish improvement over the matching incumbent, and is not a leaderboard score estimate.
- Strict local format checks pass against a hash-pinned owner-mirror template (single band, finite, `[0,1]`, EPSG:32611, `3730×3292`, transform match). The template is not organizer-authenticated.
- Literal uniqueness **fails**: registry scan reports surface max absolute Spearman `0.212714`, but final-dot overlap reaches `99.8035%` against the registered 5-pixel calibration lattice; other listed rasters exceed the `70%` threshold too. Do not upload.
- Scientific integrity **fails**: `Band 6 (tc)` was treated as magnetic tilt although prior repository forensics identify it as radiometric Total Count. This artifact is preserved for audit, not promotion.
- The assigned lane paragraph is missing and total experiment/time accounting is incomplete. No weekly slot was used.

This TIF is intentionally **not presented as a submission download**. The portal and release gate are fail-closed. The latest card and review have precedence over stale historical pages or earlier candidate cards.

## Reproduction and checks

Competition data are login-walled on DrivenData in this environment. Hash-pinned public GitHub mirrors can restore a small test template, but mirror provenance is not organizer authentication. To install project dependencies and run the suite:

```bash
python -m venv .venv
.venv/bin/pip install -e . pytest
.venv/bin/python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_release_status.py
```

To restore only a format-validation template without the full data stack, use a minimal manifest containing the `sample_submission` entry; the restore script writes `data/restore_receipt.json`, so preserve or review that tracked receipt when doing so. The full feature stack and most external data are not included in Git; see `registry/data_manifest.json` and `scripts/restore_data.py`.

## Trusted starting links

- [DrivenData competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), and [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login required for competition files).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN data record](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [DOE INGENIOUS project](https://gbcge.org/current-projects/ingenious/).
- [Official competition technical report](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

Sources and provenance notes are maintained in [`registry/sources.json`](registry/sources.json) and [`docs/sources.html`](docs/sources.html). Official source links are provided for review; data-derived claims remain conditional on their recorded provenance.
