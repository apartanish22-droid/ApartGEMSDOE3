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

## Three-pass re-review and nine-site decision table

The request called for multiple passes. The following is the result of three distinct review passes, not three model experiments:

1. **Pass 1 — implementation/inventory:** inspected the portal, README/charter, current release registry, holdout evaluator, submission writer/validator, site-audit script, tests, and Pages workflow. The project already has a fail-closed release flow and a four-hypothesis research shortlist; it does not have the assigned method-lane paragraph or the data required for a new experiment.
2. **Pass 2 — verification/edge cases:** installed dependencies in ignored `.venv/`, restored only the two SHA-256-pinned owner-mirror format inputs (label mask and template) to ignored `.cache/`, then ran tests and release checks. Result: **109 passed, 2 skipped**; `check_release_status.py` passed and kept `ok_to_submit=false`. Strict full-array format validation of the recorded negative candidate passed against the owner-mirror template. That pass verifies file structure only. The fresh nine-site audit command was also run and stopped at the first absent source raster, `.cache/registry/GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`.
3. **Pass 3 — original-request reconciliation:** no new TIF was generated, no holdout experiment was run, no current leaderboard value was asserted, and no slot was used. This is intentional: method lane, feature stack/training raster, full comparison registry and fresh source artifacts are missing. Producing a TIF now would not satisfy the protocol's scientific validation and uniqueness requirements. The nearest recorded artifact remains explicitly **DO NOT SUBMIT**.

### Focus-site table (archived evidence, not a live refresh)

The table below transcribes the pinned nine-site byte-audit (`evidence/nine_site_best_files_audit.json`) and the owner-supplied score claims already quoted in the project brief. The nine-site raster comparison was run against the recorded archived variants, but could not be independently refreshed in this checkout because those source rasters are absent. `OWNER-REPORT` scores are not presented as organizer-confirmed receipts. For a new submission, a numerical leaderboard score estimate is **not estimable**; a holdout DTI is not a calibrated leaderboard score.

| Site | Archived best file | Reported score | Estimate for a new raster | Unique vs the other eight? |
|---|---|---:|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | OWNER-REPORT 0.2477 | Not estimable | No — 100.00% of its dots within 3 px of GEMSDOE25 in the archived audit |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | OWNER-REPORT 0.2600 | Not estimable | No — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | OWNER-REPORT 0.2449 | Not estimable | No — 98.02% within 3 px of GEMSDOE24 |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | OWNER-REPORT 0.2710 | Not estimable | No — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | OWNER-REPORT 0.2600 | Not estimable | No — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | OWNER-REPORT 0.2708 | Not estimable | No — 100.00% within 3 px of GEMSDOE24 |
| **GEMSDOE32** | **`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`** | **OWNER-REPORT 0.2778 — highest of these nine** | Not estimable | No — 100.00% within 3 px of GEMSDOE24 |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | OWNER-REPORT 0.2632 | Not estimable | No — 99.71% within 3 px of GEMSDOE27 |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | OWNER-REPORT 0.2750 | Not estimable | No — 97.58% within 3 px of GEMSDOE27 |

These are audit identifiers, **not download recommendations**: copying or resubmitting a listed raster is not authorized. The archived audit reports shape 3730×3292, EPSG:32611, one band for the variants, and checksum agreement with its pinned manifest. It is not a fresh organizer-side validation. It also contains Spearman values; an absolute rank correlation above 0.90 is another duplicate stop. The exact filenames and source repositories are recorded in `registry/focus_registry_manifest.json` and the table source audit.

### Why the GEMSDOE32 result is not an actionable score recipe

The supplied evidence places the GEMSDOE32 0.2778 owner-reported result above the other eight focus-site values. The repository's [`knowledge/03_why_02778_and_the_anatomy_of_the_family.md`](../knowledge/03_why_02778_and_the_anatomy_of_the_family.md) treats the score movement in its nested thinning/pruning family as consistent with reducing low-credit false-positive mass. That is a plausible explanation, **not a causal identification**: there is no randomized intervention or hidden truth receipt establishing which pixels caused the score gain. The artifact is itself a member of a near-identical raster family according to the archived overlap analysis, and it is already reported submitted. It is therefore learning evidence, not a candidate to copy or resubmit.

A date/claim discrepancy also remains: the user prompt calls 0.3195 the current leaderboard high, while the repository's cached status records an official public-page observation of 0.4437 on 2026-10-26. Neither is freshly checked in this review, so neither should be described as today's current value. The only safe current wording is “live leaderboard not refreshed; consult the official [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).”

### Additional irregularity: literal dot-overlap gate can constrain candidate size

`evidence/irregularities_ledger.json` records a geometric check against a dense 5-pixel calibration lattice: only 6,649 footprint cells were farther than 3 pixels from that lattice. Under the literal rule “no more than 70% of candidate dots may be within 3 px,” a candidate larger than 22,163 dots cannot satisfy this one registry comparison (because at most 6,649 dots can be outside the buffer). The nine focus submissions contain 37,654–61,328 dots and accordingly fail the archived focus-cohort overlap checks. Do **not** silently exempt the lattice or reinterpret this limit; raise it as a protocol-level review issue before spending an experiment or slot. A candidate below that size is not automatically unique or scientifically useful.

## Evidence card

Machine-readable review card: [`evidence/repo_review_20261030.json`](../evidence/repo_review_20261030.json). It records this as a negative review with no experiment, no new raster, no score estimate, and no submission authorization.
