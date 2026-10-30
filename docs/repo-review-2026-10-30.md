# Repository review — 2026-10-30

## Decision

**NEGATIVE — DO NOT SUBMIT any artifact in this checkout.** This review generated no raster and did not run a model experiment or spend a competition slot. The saved candidate checked below is only format-valid against the local owner-mirrored template; that does not make it scientifically validated, unique, or eligible to submit.

The user's requested research protocol is retained in the root [README](../README.md). This review follows its bounded-experiment and fail-closed release rules. No new “highest score” is inferred from a holdout metric.

## Review performed

- Read the README, project charter, release-status registry, nine-site executive summary, scientific/hypothesis notes, holdout evaluator, submission writer, test configuration, and Pages workflow.
- Installed project dependencies into ignored `.venv/` and restored only `labels.tif` and `sample_submission.tif` from the hash-pinned owner-mirror manifest into ignored `.cache/`. The manifest explicitly says these are **not organizer-authenticated**.
- Ran `.venv/bin/python -m pytest -q`: **109 passed, 2 skipped**, with 33 Rasterio affine deprecation warnings.
- Ran `.venv/bin/python scripts/check_release_status.py`: **PASS**, status remains fail-closed, hashes match, and no slot is recorded as used.
- Ran strict format validation on the current research-only candidate. It passes the local owner-mirror grid check: one-band float32, shape 3730×3292, EPSG:32611, matching transform, finite values, and values in [0,1]. This is a structural validator result only, not an organizer acceptance receipt.
- Attempted to rerun `scripts/audit_nine_site_best.py`; it stopped because the locally cached GEMSDOE24 source raster is absent (`.cache/registry/...`). No overlap result was independently recalculated in this review.

The starting checkout did not have the local sample/label files; this was a reproducibility prerequisite for two tests, not a source-code defect. After restoring the pinned mirrors, all tests passed.

## Findings and irregularities

### Release / data gates

1. **No submission is currently safe or authorized.** The latest recorded candidate is `H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS` (SHA-256 `8d90342de3a9d62bb718ea209ed5644cca0878eff906029dbc975da438cdcafd`). Its recorded HOLDOUT-DTI is weak, single-feature canaries are absent, full-registry surface/final-dot comparison is absent, and the session method lane is not specified. The current status JSON correctly marks it negative and `ok_to_submit=false`.
2. **A valid file format does not establish a good submission.** The strict local validator passes that raster, but only against an owner-mirrored template. The DrivenData data page is login-walled in this project record; the official submission-page receipt is also absent. Therefore neither exact organizer compatibility nor score is confirmed.
3. **The data needed to test a new hypothesis is not present.** The checkout lacks the 19-band training raster, cached feature stack, complete registry rasters, and the GEMSDOE24 files required by the site-audit script. The training raster manifest entry is about 419 MB and describes an owner mirror, not an authenticated competition download. No holdout canary, holdout comparison, or fresh nine-site overlap audit was run.
4. **The assigned lane is missing.** The request refers to a method paragraph that assigns one lane, but no such single method paragraph is present in the project instructions available to this checkout. Do not choose an experiment lane by guessing.
5. **Historical leaderboard claims remain evidence-classed correctly.** The repository's executive summary labels the nine-site scores OWNER-REPORT, not ORGANIZER-CONFIRMED. It reports 0.2778 for GEMSDOE32 as the largest of the provided nine-site results; no receipt ties that score to the exact raster bytes in this checkout. A score estimate for a new candidate is not estimable from the evidence here.
6. **A fresh site audit is not reproducible locally yet.** `scripts/audit_nine_site_best.py` expects the original candidate rasters in `.cache/registry/`; they are not present. Its existing checked-in audit records are historical evidence, not a live refresh.
7. **CI is appropriate as a safety net but not evidence of current scientific validity.** The Pages workflow runs tests, release-state checks, and format checks for historical rasters. It does not run a new model, holdout, canary, or fresh registry audit; publication can only demonstrate those checks on the checked-out evidence. The status copy appropriately says no candidate is authorized.

## Hypotheses worth considering after the blockers are cleared

The repository already documents a four-item shortlist in [next-hypotheses-review-20261028.md](research/next-hypotheses-review-20261028.md). Its ranking is qualitative, not a DTI forecast. The leading idea is a multi-scale gradient ridge in competition band 15 (`depth_to_base_surf`) with a weak-surface-expression gate using band 12 (`det_elev`). It aims at buried basement steps that may have no mapped scarp; sedimentary facies edges, paleochannels, and interpolation seams are plausible non-fault mimics. A related H61-1 idea is already registered as unvalidated, so this is not asserted to be globally novel.

Other shortlist ideas are directional semivariogram anisotropy of residual gravity/magnetic fields; signed, scale-persistent magnetic–gravity edge offset; and paired signed cross-front topographic profile residual. Each has plausible non-fault mimics and distinctness caveats documented in that proposal. The proposal identifies in-repository layers, so no new outside layer is required for those initial tests; however, band semantics and data availability still need local byte-level confirmation. **No candidate was selected or tested in this review.** If a later hypothesis requires USGS 3DEP, the official source pointer is [USGS 3DEP](https://www.usgs.gov/3d-elevation-program); current availability and the exact necessary tiles must be checked before treating it as a viable input.

## Recommended next work

1. Restore and hash-check the complete, permitted input set and feature cache; distinguish organizer downloads from owner mirrors in provenance.
2. Restore the full registry and GEMSDOE24/25/27/28/30/31/32/33/36 top rasters so the specified uniqueness audit is reproducible.
3. Record the single assigned method lane and a fresh experiment budget before running anything.
4. Reconcile evaluator/writer versions and band semantics; run per-feature leakage canaries before trusting a model feature.
5. Run no more than three pre-registered experiments using shared `evaluate_holdout.py` and `submission_writer.py`, fold-local visible-only catalogue features, exact masking, and pooled DTI with the specified kernel. Compare paired spatial confidence intervals to a same-evaluator incumbent.
6. Apply literal registry checks to both the unplaced surface and final dots; stop at either specified duplicate threshold. Validate the exact saved bytes against an authenticated competition template and preserve all evidence in a run card.
7. Keep slot selection separate. Only show an “OK TO SUBMIT” download link after scientific, uniqueness, format, and selector gates pass; capture the organizer receipt afterward.

## Evidence card

Machine-readable review card: [`evidence/repo_review_20261030.json`](../evidence/repo_review_20261030.json). It records this as a negative review with no experiment, no new raster, no score estimate, and no submission authorization.
