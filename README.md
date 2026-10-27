# ApartGEMSDOE3 — evidence-first DOE GEMS research

> **Persistent starting brief — read before every work session.** Maximize P(Win) through auditable geological discovery, not optimistic score projections. Own the complete outcome. A valid GeoTIFF, uniqueness check, holdout score, organizer score, and permission to use a weekly slot are different things; never conflate them. No manual-inspection step is an automated validation gate.

## Current release decision

**Research TIFF available: YES. OK to submit: NO — DO NOT SUBMIT.** The existing candidate is the prior MRCJ run artifact, not a new TIFF generated in this review. It passes pairwise checks against the nine historical rasters tracked locally and strict `[0,1]`/grid checks inside the template footprint, but the official null-outside instruction is not met (exterior values are zero), its archived scientific card does not satisfy the current selector contract, no current-best paired comparison or independent replay is available, and weekly quota is unverified. A current external owner page also reports a 3-pixel lattice that would conditionally force at least 82.34% overlap for any 37,654-dot candidate; that lattice is not in this checkout and was not independently replayed. A stale original run card says `promote`; the current exact-file selector review supersedes that wording and fails closed. No competition slot has been used.

- Research artifact: [`apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif`](docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif)
- Current fail-closed review: [`docs/data/latest-run-card.json`](docs/data/latest-run-card.json)
- Human-readable decision and nine-site table: [`docs/index.html`](docs/index.html), [`docs/executive-summary.html`](docs/executive-summary.html), and [`docs/executive-summary.md`](docs/executive-summary.md)
- Supplemental research slate and future workflow: [`docs/hypotheses.html`](docs/hypotheses.html) and [`docs/submission-guide.html`](docs/submission-guide.html)
- Original experiment card (immutable prior record; not current upload authorization): [`evidence/run_card.json`](evidence/run_card.json)

The prior experiment reports **HOLDOUT-DTI 0.022070** (`gems-segment-pooled-v1`, `60,988` withheld positives, spatial-block bootstrap 95% CI `[0.017237, 0.026923]`). This is internal hide-and-recover evidence, not an organizer score or a leaderboard estimate. No defensible leaderboard-score estimate is available. The user's two overall-high-score claims (`0.3195`, `0.4413`) conflict and neither is linked to a submission-page receipt here.

## Persistent project aims

- Maintain an executive evidence review for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36. Historical owner claims—including GEMSDOE32 H33-B2 at `0.2778`—are unverified unless linked to an organizer submission receipt; its `0.2747` PR projection is not a score.
- Seek physically grounded, genuinely distinct fault hypotheses with named non-fault mimics and verified free official sources. Rank candidates before implementation and check current parallel method lanes and registry freshness.
- Aim to maximize the chance of winning, including ultimately outperforming reported leaders, but never manufacture a score projection or claim that a target is achieved without comparable HOLDOUT-DTI evidence and organizer receipts.
- Produce a downloadable single-band GeoTIFF only when data provenance, unique status, exact CRS/grid/range/nodata validation, holdout evidence and selector gates are established automatically. A research download is not submission approval.
- Treat the three-experiment/two-hour limit as a hard stop; do not use or select a competition slot as part of research. The prior experiment allowance is currently exhausted.

## Non-negotiable parallel-run protocol

1. Stay inside the explicitly assigned method lane. The prompt's promised single-method paragraph is absent from the materials available to this branch, so no further experiment is authorized until the active lane is recorded. Before placement and on final dots, check absolute Spearman rank-correlation against every registry raster; stop if `|rho| > 0.90` or more than `70%` of dots lie within `3 px` of any registry raster. Our fresh audit is scoped to the nine tracked focus rasters only.
2. Reuse the template's cached feature stack, shared `evaluate_holdout.py`, and shared `submission_writer.py` where present. Do not fork the metric/writer. Holdout hides complete fault components with a buffer; catalogue-derived features use visible faults only; visible faults are masked pixel-exactly; pooled DTI uses `alpha=0.2`, `beta=0.8`, and the `300 m` triangular kernel.
3. Label a score only as `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` from a submission-page receipt. Label other metrics by their type. A projection is never a score.
4. Test every feature alone on the holdout. AUC above `0.90` is presumed leakage until proven otherwise.
5. End each run with a machine-readable card: hypothesis, mechanism, non-fault mimic, holdout DTI/CI, correlation and overlap, raster SHA-256, validator output, submission name/note (<=140 characters), and `promote` or `negative` verdict. Negative results are deliverables.
6. Stop after three experiments or two hours. A selector—not a model runner—decides whether a weekly slot may be used. Never upload automatically.
7. Do not let a format-only pass or a file download button imply slot authorization.

## Submission-format preflight

The official [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) requires one float32 GeoTIFF band, same template CRS/grid/resolution/bounds, values in `[0,1]`, and null/NaN outside the bounds. Use `src/gems/submission.py` and `scripts/submission_writer.py`; the preflight is deliberately separate from scientific promotion. The candidate currently passes the in-footprint strict range and sample-grid checks, but the current release audit reports `official_format_compliant: false` because its exterior is zero, not null/NaN. Do not upload it.

Re-run the read-only audit (no geological experiment or submission slot is used):

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/review_current_artifact.py
.venv/bin/python -m pytest -q
```

## Data, provenance, and limitations

This checkout now contains an owner-mirrored sample/template, known-fault masks, GeoDAWN-derived extensions, the nine focus-site comparison rasters, and the MRCJ research TIFF. The geophysical extension manifest cites the official USGS GeoDAWN data release and records archive checksums; the mirrored submission template is not from an authenticated DrivenData session. The original full competition training features, all external/concurrent submission rasters, complete up-to-date registry manifest, a matched current-best paired holdout card, submission-page receipt, and quota verifier are not present. These are blockers, not facts to infer.

The current selector correctly fails closed when current-best evidence, complete registry/peer evidence, exact-file C2ST, independent replay, or organizer quota evidence are missing. Do not weaken it or re-label the MRCJ result to get a positive status.

## Official sources

- [Competition page, rules, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
- [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN source record](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) · [DOI](https://doi.org/10.5066/P93LGLVQ)
- [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [USGS stress dataset](https://data.usgs.gov/datacatalog/data/USGS:5cf6e143e4b0d63728b9b49a)
- [DOE geothermal data resources](https://www.energy.gov/hgeo/geothermal/technical-resources) · [GDR 1391](https://gdr.openei.org/submissions/1391)
- External registry hazard (owner-reported; not independently reproduced in this checkout): [GEMSDOE28 current page](https://buffedlizard55-lab.github.io/GEMSDOE28/) · [GEMSDOE31 status](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

## Next work

1. Reconcile the stale original `promote` card with the current negative selector status; preserve both provenance records without implying the old promotion is active.
2. Supply the missing same-evaluator current-best and paired baseline receipts, full up-to-date registry manifest/rasters (including concurrent submissions), lane assignment, and independent C2ST/replay evidence.
3. Use the existing registered candidate and experiment evidence as research only. Do not spend another experiment until the current best and the active lane are established; the previous three-experiment budget is already exhausted.
4. Obtain authenticated organizer template/format confirmation and current weekly-cap status; then generate a new TIFF only after a candidate beats the current holdout best and all novelty/format gates pass.

No new submission should be described as submit-ready until the separate selector returns `OK_TO_SUBMIT` with complete evidence. At present it returns `DO_NOT_SUBMIT`.
