# Repository review — 2026-10-30 (verified pass update)

## Executive decision

**NEGATIVE — DO NOT SUBMIT any artifact in this checkout.** No new raster was generated, no model experiment was run, and no competition slot was used. The current recorded candidate is a negative research artifact, not an approved submission. Structural validity against the local owner-mirrored template does not establish scientific quality, uniqueness, organizer compatibility, or submission eligibility.

The persistent project brief and parallel-run/release protocol are in the root [README](../README.md); read it first in each session. The prompt's reference to an assigned “single method paragraph” does not specify an identifiable method lane in the prompt or checkout. Do not infer one.

## Three-pass review

### Pass 1 — repository, scores, and provenance

- Reviewed the README/project charter, current status registry, executive/release pages, source/evidence manifests, latest run cards, holdout/writer code, tests, Pages workflow, and ranked hypothesis shortlist.
- The shared evaluation and writing entry points are `scripts/evaluate_holdout.py` and `scripts/submission_writer.py`. Release status correctly fails closed; its current `ok_to_submit` state is false.
- The pinned cohort audit already recorded in `evidence/nine_site_best_files_audit.json` reports that all nine selected focus-site TIFFs were SHA-256 checked against refs in `registry/focus_registry_manifest.json`. These are owner-maintained GitHub mirrors; this verifies mirror integrity against the manifest, **not** organizer provenance or a score receipt. This continuation did not restore those nine files.
- That archived/recomputed cohort audit has 36 site pairs. **All 36** breach the directional `>70%` within-3-pixel overlap gate in at least one direction; **11/36** also have absolute footprint Spearman correlation `>0.90`. Thus none of the selected nine files is unique against this cohort under the literal rule. It does not establish uniqueness for any new candidate against the complete registry.
- All nine score claims below are `OWNER-REPORT`, not `ORGANIZER-CONFIRMED`: no submission-page receipt connecting the exact selected raster hash to each reported score is stored here.

### Pass 2 — science, data, and release gates

- The full 19-band competition training raster and cached feature stack are absent from `data/` and `.cache/gems_data`. The complete registry is also not restored; only the nine selected rasters were fetched for the cohort audit.
- `labels.tif` and `sample_submission.tif` were restored from hash-pinned owner-mirror entries into ignored `.cache/gems_data`. The sample template is useful for local format checks, but is not organizer-authenticated.
- The current negative research candidate `H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS` has a recorded HOLDOUT-DTI diagnostic of `0.002126` (evaluator `GEMSDOE32-HOLDOUT-v3-visible-gated`, 22,232 withheld positives, 95% CI `[0.001567, 0.002606]`), but single-feature canaries are missing, a full-registry uniqueness audit is missing, and there is no paired same-evaluator improvement evidence. This number is **HOLDOUT-DTI**, not a leaderboard estimate.
- A strict local format check of that recorded candidate passes against the hash-pinned owner-mirror template: one-band float32, shape `3730×3292`, EPSG:32611, affine transform match, finite array, and values in `[0,1]`. This does not make it eligible or organizer-validated.
- No compliant new experiment was possible: no feature-alone leakage canary; no fold-local buffered whole-segment hide-and-recover; no same-evaluator paired incumbent comparison; and no surface/final-dot comparison for a new candidate. No new score estimate is supportable.
- Historical GEMSDOE32 `0.2778` is the highest value in the supplied nine-site cohort, still `OWNER-REPORT`. Pruning predictions with low hidden-truth marginal credit is plausible as an explanation of a score change, but nested artifacts and a reported leaderboard score do not prove causality. The older user-supplied `0.3195` and cached public leaderboard observations are time-specific claims, not a current live check or candidate score.

### Pass 3 — executable checks and edge cases

- Created ignored `.venv/`; installed declared `requirements.txt`. The system Python lacked NumPy and pytest.
- Restored the two minimal pinned test/format inputs using `scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json`. Initial test failures were caused by those absent files; after restoration, the full suite passed: **109 passed, 2 skipped**. The two skips are not passes. There were 33 Rasterio affine `PendingDeprecationWarning`s.
- `python scripts/check_release_status.py` → **PASS**: fail-closed status and hashes agree; portal current; no slot used.
- The previously recorded nine-site audit reports **PASS** after restoring the nine selected TIFFs from pinned refs. In this continuation, the same audit command stopped at the missing first `.cache/registry/GEMSDOE24/...` raster; no fresh pairwise computation was completed here. The recorded hash-verified audit output is used as historical evidence, not a newly reproduced result.
- `python3 -m compileall -q src scripts tests` and `git diff --check` were recorded as **PASS** in the incoming same-date review. This continuation reran `git diff --check` successfully; compileall was not rerun after integrating that update.
- No TIF generation, feature fitting, leaderboard fetch, or model experiment was performed in this continuation.

## Nine-site executive table

The values are the highest scores supplied for these sites, not newly checked live scores or organizer receipts. Cohort uniqueness is computed from the nine selected raster bytes only. New score estimate: **not estimable**.

| Site | Archived highest-reported file (not a download recommendation) | Score evidence | New-candidate leaderboard estimate | Cohort uniqueness | Decision |
|---|---|---:|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | OWNER-REPORT 0.2477 | Not estimable | FAIL — 100.00% within 3 px of GEMSDOE25 | Archive only; do not resubmit |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | OWNER-REPORT 0.2600 | Not estimable | FAIL — 100.00% within 3 px of GEMSDOE24 | Archive only; do not resubmit |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | OWNER-REPORT 0.2449 | Not estimable | FAIL — 98.02% within 3 px of GEMSDOE24 | Archive only; do not resubmit |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | OWNER-REPORT 0.2710 | Not estimable | FAIL — 100.00% within 3 px of GEMSDOE24 | Archive only; do not resubmit |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | OWNER-REPORT 0.2600 | Not estimable | FAIL — 100.00% within 3 px of GEMSDOE24 | Archive only; do not resubmit |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | OWNER-REPORT 0.2708 | Not estimable | FAIL — 100.00% within 3 px of GEMSDOE24 | Archive only; do not resubmit |
| **GEMSDOE32** | **`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`** | **OWNER-REPORT 0.2778 — top of focus nine** | **Not estimable** | **FAIL — 100.00% within 3 px of GEMSDOE24** | **Archive only; already reported submitted; do not resubmit** |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | OWNER-REPORT 0.2632 | Not estimable | FAIL — 99.71% within 3 px of GEMSDOE27 | Archive only; do not resubmit |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | OWNER-REPORT 0.2750 | Not estimable | FAIL — 97.58% within 3 px of GEMSDOE27 | Archive only; do not resubmit |

The archived files are identifiers for forensic review, not “OK to submit” downloads. GEMSDOE32 is the top reported entry in this nine-site comparison, but it was already reportedly submitted and is not a unique alternative. A `Not estimable` entry means no defensible calibration maps holdout DTI to leaderboard score; it is not a score of zero. **Literal-overlap constraint flagged:** the archived irregularity records for the 13GEMS r13-lattice-s5 calibration raster report 6,649 footprint cells outside its 3-pixel buffer, implying that no more than 22,163 dots can meet the literal 70% overlap cutoff against that raster. That is below every 37,654–61,328-dot focus file, and the recorded 0.2778 champion itself exceeds the cutoff. This conflicts with the intended use of a uniqueness gate as a discriminative test. Do not silently exempt the calibration raster; an owner-level prospective decision is required before using this rule for promotion. Until resolved, no dense candidate can be called unique under the literal gate. See `evidence/arena51_run_card.json`, `evidence/h45_tworegime_run_card.json`, and `evidence/irregularities_ledger.json` / `IR-51-LATTICE-01`.

The exact byte hashes, grid facts, positive-dot counts, and pairwise results are in [`evidence/nine_site_best_files_audit.json`](../evidence/nine_site_best_files_audit.json). GEMSDOE32's score anatomy and explicit causal limitations are documented in [`knowledge/03_why_02778_and_the_anatomy_of_the_family.md`](../knowledge/03_why_02778_and_the_anatomy_of_the_family.md).

## Ranked hypotheses before implementation

The four in-band proposals already documented in [`research/next-hypotheses-review-20261028.md`](research/next-hypotheses-review-20261028.md) remain proposals only. These qualitative rankings are neither measured DTI estimates nor authorization to select a method lane.

1. **Buried cover-thickness ridge with surface-quiescence gate.** Competition depth-to-base and elevation layers; multi-scale gradient ridge of cover thickness gated on weak surface slope/curvature. Could target a buried fault block boundary without a catalogued scarp. Mimics: depositional facies edges, paleochannels, interpolation seams. Qualitative utility: medium (highest in this shortlist); cost: medium. Related H61-1 work is unvalidated, so global novelty is not claimed.
2. **Directional semivariogram anisotropy of potential-field residuals.** Gravity and verified magnetic layer; compare along-strike vs cross-strike residual dependence. Could emphasize concealed corridors not captured by local edge strength. Mimics: lithologic grain, aligned stratigraphy, survey artifacts. Utility: low–medium; cost: medium–high.
3. **Signed cross-edge magnetic–gravity offset persistence.** Verified magnetic and gravity fields; track signed edge displacement along the local normal across scale. Could target fault-related source-depth separation. Mimics: intrusive contacts, source-depth changes, survey seams. Utility: low–medium; cost: medium; adjacency to prior multi-physics work is high.
4. **Paired signed cross-front topographic-profile residual.** DEM derivatives and competition elevation; test paired flank profile asymmetry where direct scarp expression is weak. Could target subtle tectonic tilt. Mimics: fans, differential erosion, roads, seams. Utility: low; cost: medium; the local seamless DEM is unavailable.

No idea was run because the lane is unspecified and required data are absent. The first three use in-competition layers and need no new external data source for initial tests; the fourth needs a local DEM source restored and verified. If further work requires public terrain data, the official pointer is [USGS 3DEP](https://www.usgs.gov/3d-elevation-program); exact coverage and availability must be checked before treating it as viable.

## Review run card — no experiment

```json
{
  "hypothesis": "No new hypothesis tested: assigned method lane is unspecified and required predictor stack is unavailable.",
  "mechanism": "N/A — repository review only; no feature fitting or raster generation.",
  "named_non_fault_mimic": "N/A for an unrun candidate; shortlist mimics are documented in docs/research/next-hypotheses-review-20261028.md.",
  "holdout_dti": "NOT RUN in this review; do not substitute the earlier candidate's HOLDOUT-DTI diagnostic.",
  "correlation_overlap_vs_registry": "No new raster. The nine selected historical files: 36/36 pairs breach directional >70% within-3-pixel overlap; 11/36 pairs have |Spearman| >0.90.",
  "raster_sha256": null,
  "validator_output": "No new TIF. Existing negative candidate passes local owner-mirror structure/range check only; release-status check PASS. Organizer template not authenticated.",
  "submission_name": null,
  "submission_note": "Review only; no candidate, download authorization, or slot selection.",
  "verdict": "negative"
}
```

Machine-readable companion card: [`evidence/repo_review_20261030.json`](../evidence/repo_review_20261030.json). It is a review card, not a candidate run card.

## Highest-priority follow-up and limitations

1. Restore competition-origin feature data and cached stack using permitted authenticated access; record hashes and provenance. Owner mirrors are not organizer authentication.
2. Resolve and preregister the one method lane and stop rule before experiment work.
3. Run shared fold-local buffered hide-and-recover with visible-only catalogue-derived features, exact masks, feature-alone canaries, pooled DTI and spatial paired 95% CI against a same-evaluator incumbent.
4. Restore the complete registry before checking any candidate surface before placement and final dots after placement; stop on either duplicate threshold.
5. Keep selector authorization separate from holdout/format status; do not spend a slot on an unvalidated idea. Record the organizer receipt and exact file hash if selected.
6. Consider fixing the affine deprecation warnings centrally, and keep clean-checkout CI provisioning the minimal pinned format inputs.

## Official source pointers for review

- [DrivenData competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)

These links are pointers for human source review; they were not all live-fetched in this restricted review. The nine selected raster bytes were fetched from pinned owner GitHub repositories; their reported scores remain unconfirmed.

## Session verification and provenance (2026-10-30)

This table distinguishes checks rerun in the current continuation from same-date checks preserved in the incoming main-branch review/evidence. Historical or merged-in evidence is not described as a fresh run here. Nothing below is a score, a new raster, or a submission authorization.

| Check | Command or source | Result |
|---|---|---|
| Competition data reachable? (recorded earlier same-date check) | Previous run card `evidence/repo_review_20261030.json` | It records HTTP 000 for DrivenData, Dropbox, GDR/OpenEI, and USGS, and HTTP 200 for GitHub/PyPI/npm. Not rechecked in this continuation. |
| Pinned core owner-mirror inputs (rerun here) | `scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json` | Restored `labels.tif` and `sample_submission.tif`; hashes match the manifest. These come from a third-party competitor's GitHub repo (`buffedlizard55-lab/GEMSDOE24`), not the organizer. The large 19-band training raster was not fetched. |
| Test suite (rerun here) | `.venv/bin/python -m pytest -q` | 109 passed, 2 skipped, 33 Rasterio affine deprecation warnings. |
| Release gate (rerun here) | `scripts/check_release_status.py` | PASS: candidates fail closed, hashes match, no slot used. |
| Format check, current negative candidate (rerun here) | `scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite docs/downloads/gemsdoe32-apart3-unique-offcatalogue-geophys-20261028T225009Z-22727d79-zeros.tif` | PASSED structure and whole-array [0,1]/finite checks against owner-mirror template; SHA-256 `8d90342de3a9d62bb718ea209ed5644cca0878eff906029dbc975da438cdcafd`. Not organizer authentication or authorization. |
| Format check, GEMSDOE32 0.2778 archive (recorded earlier same-date check) | Earlier run recorded in this review/evidence | The 0.2778 file passed format/range checks against the owner-mirror template; SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. It is a copy of a prior submission and is **not** a candidate. Score remains OWNER-REPORT (IR-32-SCORE-01/02/03). |
| Nine-site audit in this continuation | `.venv/bin/python scripts/audit_nine_site_best.py` | BLOCKED at the first missing file in `.cache/registry/`; no fresh calculation here. The checked-in audit is separately recorded as hash-verified in the incoming prior review. |
| Leaderboard top, conflicting figures (snapshot inspection only) | `docs/data/feed.json`, `evidence/live_leaderboard_snapshot_20261026.json`, `registry/leaderboard_snapshot_2026-10-04.json` | Stored observations: 2026-10-04 #1 nchuzhoy 0.3262 (0.3195 was #3, DARD); 2026-10-25 #1 xiaofanhu 0.4413; 2026-10-26 #1 xiaofanhu 0.4437. No live fetch was done here; the most recent stored observation is not today’s current value. Public values are not organizer receipts for any GEMSDOE file. |
| Leaderboard top, conflicting figures | `docs/data/feed.json` (verified snapshots), `evidence/live_leaderboard_snapshot_20261026.json`, `registry/leaderboard_snapshot_2026-10-04.json` | The prompt cites **0.4413** and **0.3195**. The repo's snapshots show: 2026-10-04 #1 nchuzhoy 0.3262 (0.3195 was #3, DARD); 2026-10-25 #1 xiaofanhu 0.4413; 2026-10-26 #1 xiaofanhu **0.4437**. The most recent verified figure in the repo is 0.4437. Public leaderboard values are not organizer receipts for any GEMSDOE file. |
| Internal evidence-class conflict | `docs/data/feed.json` entries that label 0.2778 as ORGANIZER-CONFIRMED vs OWNER-REPORT; `registry/irregularities.json` IR-32-SCORE-01/02/03 | Already flagged in the repo. The later Round-6 rule (OWNER-REPORT) governs. The ORGANIZER-CONFIRMED wording is a stale label and should be removed in a future cleanup. |

### Consequences for the user's goals

- **No unique, validated, downloadable submission was produced in this session.** Producing one needs the 19-band training raster and the cached feature stack, which are not in this checkout and are not reachable from the sandbox. A raster built from the two restored label/template files alone would not be a validated model and would fail the README gates.
- **No score estimate is given** for a new file. The estimate is "not estimable" until a holdout experiment runs.
- **The existing four-candidate shortlist** in `docs/research/next-hypotheses-review-20261028.md` is the current hypothesis set. This session did not add new hypotheses, because each one would need the same blocked data before any test could run.
- **Two actions for the owner:** (1) decide whether the 19-band training raster may be restored from a non-organizer mirror, or whether an organizer-authenticated copy can be placed in `data/` manually; (2) supply the single assigned method paragraph the protocol refers to.
