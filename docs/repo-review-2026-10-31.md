# Repository review — 2026-10-31

## Executive decision

**NEGATIVE — do not download or submit any artifact from this checkout.** This review generated no candidate raster, ran no geological experiment, and used no competition slot. The existing release gate is explicitly fail-closed. The most important blocker is not a lack of clever model code: the method paragraph that assigns this run's lane is absent, the full feature stack and full registry are not present in the checkout, and the strongest reported focus-site file is neither unique within the nine-site cohort nor independently tied to a score receipt.

This report is a repository and process review, not a new score result. Scores supplied by the prompt remain `OWNER-REPORT`; metric results in prior checked-in evidence retain their evaluator labels and provenance. A leaderboard-score estimate for a new raster is **not estimable**.

## Pass 1 — inventory and end-to-end trace

- Read `README.md` and `docs/PROJECT_CHARTER.md` first, then inspected status/manifest files, executive/release pages, prior session reviews, the nine-site evidence, shared evaluator/writer entry points, tests, and CI workflow.
- `README.md` correctly carries the core objective and insists on an explicit download/submission verdict. `scripts/evaluate_holdout.py` delegates to `gems32.holdout`; `scripts/submission_writer.py` is the shared writer. The web release gate checks that current and historical artifacts remain unauthorized.
- The existing executive-summary page already has a per-site table for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36; it says no new-score estimate is supportable and provides no download CTA. The current reported best is GEMSDOE32's `0.2778` (`OWNER-REPORT`), not an organizer-confirmed score. The checked-in nine-site audit says its selected bytes are not unique within the cohort.
- The pipeline has a substantial history of research implementations and negative run cards. No blank-slate model rebuild is justified. The README itself records protocol overruns and duplicate outcomes in previous exploratory work; those are evidence to keep the next run fail-closed, not permission to exceed the current budget.

## Pass 2 — scientific, uniqueness, release, and site review

### Focus-site claims and why 0.2778 is not explained causally

The nine-site audit and `docs/research/nine-site-verification-20261030.md` record the submitted-file names, owner-reported scores, byte hashes, validations, and pairwise overlap results. In that record, GEMSDOE32 at 0.2778 is the top reported value of this cohort and GEMSDOE36 is next at 0.2750; the small reported gap is not supported as a real ordering by the documented uncertainty. All 36 pairs among the selected nine exceed the literal 70%-within-3-pixel overlap threshold in at least one direction; 11/36 also exceed the |Spearman| 0.90 gate. GEMSDOE25 and GEMSDOE30 are identical after NaN-to-zero normalization. These are cohort-only results, not a full-registry uniqueness audit.

The repo's strongest *explanation* is a hypothesis, not a proven causal result: pruning dots near the existing USGS fault catalogue may remove false-positive mass because the public test target is described as new faults not in that catalogue. A documented nested thinning sequence is consistent with this. But those are related artifacts, and the prompt's leaderboard scores are not receipts linked to those exact raster hashes. The existing calibration analysis also says the catalogue hide-and-recover holdout alone is not a reliable selection signal for live score. Therefore the repo cannot honestly say why the exact 0.2778 score occurred, nor establish that a new candidate will beat it.

### Registry and submission safety

- The full 451-raster registry uniqueness run is not evidenced as complete for a new candidate. No new surface was tested before placement; no new final-dot comparison exists.
- `registry/current_status.json` points to the negative `H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS` artifact (recorded 2026-10-28), with `ok_to_download: false`, `ok_to_submit: false`, and `slot_used: false`. The current release-status command agrees.
- The run protocol refers to one specific method paragraph, but it is not present in the prompt as received or in the repo. Selecting Euler, gravity/magnetic, or another lane on the user's behalf would invent the missing assignment. No experiment was started.
- Competition-format validation must be done on exact saved bytes against the official sample template, including CRS, shape, affine transform, and all values in `[0,1]`. The repo currently records that available templates are owner-mirrored, not organizer-authenticated. Prior format success against such a mirror is not authorization.
- The README, executive summary, and release portal correctly avoid presenting a file as submit-ready. Some site copy and the current status record are dated 2026-10-28/30 rather than refreshed as of this review. The release gate checks key fail-closed fields and artifact hashes, but does not establish that all prose timestamps or all research tables are fresh. This review does not claim to have re-fetched the live leaderboard.

### Three-to-four candidate shortlist — research proposals only

These are ranked by expected *decision value* and implementation cost, not a numeric DTI forecast. Their expected score lift is **not estimable** before compliant testing. Layer names are from the checked-in prepared-data manifest, which is a hash-pinned owner-mirror record; this review did not independently verify organizer provenance. The proposed validation uses the existing feature stack and evaluator, so none requires new external data to be testable once the authorized input stack and method lane are available. Novelty statements are repo code-search findings only, never proof of global novelty.

| Rank | Hypothesis and layers | Target signature / reason to find uncatalogued fault | How it differs from inspected repo methods | Named non-fault mimic | Cost / gating |
|---|---|---|---|---|---|
| 1 | **Euler structural-index-1 solution clustering** on band 14 `tmi`; numerical x/y derivatives from this continuous field. | Clusters of plausible-depth N≈1 Euler solutions that align into persistent trends could indicate a buried magnetic source boundary lacking a surface scarp/catalogue trace. | `src/gems32/tmspi.py` documents Euler N≈0 contact/depth logic, not an N≈1 clustered-solution estimator. This was a targeted code search, not proof of absent equivalent behavior elsewhere. | Magnetic dikes or mafic intrusions can generate similar solutions. | Medium. First test the single-feature leakage canary, then the assigned-lane holdout. No run until lane and feature-stack access are resolved. |
| 2 | **Gravity–magnetic cross-gradient coupling**, using bands 13 `iso_grav_anom`, 14 `tmi`, and/or 2 `rtp`. | Co-located, directionally concordant field gradients could mark a shared basement boundary under cover, including one not captured by a surface-fault catalogue. | Some multi-domain/gradient combination exists in `h35_new.py`; the proposed field pairing/physical coupling is not automatically novel. Perform direct code-level equivalence review before preregistration. | Lithologic contacts without fault displacement. | Low–medium. Existing inputs suffice; leakage canary and incremental paired holdout are mandatory. |
| 3 | **Directional residual semivariogram anisotropy**, using bands 2 `rtp` and 13 `iso_grav_anom`, after removing broad regional trends and applying catalogue distance masking fold-locally. | Persistent along-strike versus cross-strike continuity in residual potential-field texture may reveal fractured/offset basement corridors beneath cover. | Repo search found anisotropy and directional filters, but no direct semivariogram residual statistic. Similar anisotropy already exists, so this is a narrow candidate, not a claim of distinct end-to-end strategy. | Survey flight-line or processing-direction artefacts. | Medium. Needs strong acquisition-direction negative controls; features must be recomputed fold-locally. |
| 4 | **Signed cross-edge magnetic–gravity offset persistence**, using bands 2 `rtp`, 13 `iso_grav_anom`, and 18 `iso_grav_anom_hg`. | Test whether edge-normal offsets recur with consistent sign over multiple scales; a persistent offset may be compatible with faulted basement contacts at different effective depths. | The repo has joint-field and edge-like features, but no verified audit here proves the precise signed-offset persistence statistic absent. Treat as overlap risk and require direct audit before coding. | Distinct source depths and transfer functions can displace otherwise unrelated edges. | High. More design choices and confounding; lower priority unless first candidates fail. |

**Ranking caveat:** there is no evidence here to rank these by expected numerical DTI improvement. Candidate 1 is ranked first because it is clearly specified and differs from the identified N≈0 implementation, not because an unmeasured score lift is expected. Do not implement candidate 2–4 until code overlap and lane assignment are checked.

### Free official source availability

No candidate above needs additional external data for an initial test; all named layers are in the local prepared-data manifest. This does **not** mean the actual raster inputs are currently available in this checkout, or that owner mirrors are organizer-authenticated. For an external acquisition-direction control, no official source has been established or checked as obtainable in this review; do not make that a viability assumption. Official review links are listed below. The DrivenData data page may require login; no competition credentials are available to this process.

## Pass 3 — clean-environment test and release checks

Environment started without NumPy, Rasterio, or pytest. Created ignored `.venv/` and installed `requirements.txt` from PyPI. The first full test run was blocked by absent ignored inputs `.cache/gems_data/sample_submission.tif` and `labels.tif`; after restoring the two SHA-pinned core files via `scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json`, tests passed. The tracked restore receipt was returned to its original state, and the restored datasets remain ignored/untracked.

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` after restoring core inputs | **119 passed, 2 skipped**, 33 Rasterio affine `PendingDeprecationWarning`s. The two skips remain unverified scenarios, not passes. |
| `.venv/bin/python scripts/check_release_status.py` | **PASS**, fail-closed; historical/current candidate hashes match; portal's checked pointers are current; no slot used. |
| `.venv/bin/python scripts/format_audit.py --template .cache/gems_data/sample_submission.tif --out .cache/format_audit_recheck_20261031.json` | **11 pass / 6 fail of 17** downloadable TIFF variants against the hash-pinned owner-mirror template. The six failures are `-nan` variants failing the whole-array portal-safe check; this is consistent with, but does not prove the cause of, the user's portal error. Format only; not authorization. Recheck output is ignored under `.cache/`. |
| `.venv/bin/python -m compileall -q src scripts tests` | **PASS**. |
| `git diff --check` before documentation edits | **PASS**. |
| Fresh candidate generation / holdout / leakage canaries / full-registry uniqueness / organizer-template validation | **NOT RUN** — no lane assignment, full feature stack, or full registry available in this working checkout. |

Warnings and review observations:

1. The initial two test failures were environmental missing-input failures and passed after the documented pinned core restore. CI has an explicit restore step, so the clean-checkout condition is represented in workflow.
2. 33 affine deprecation warnings remain. They did not fail tests; update the shared transform construction centrally rather than suppressing warnings if compatibility work is prioritized.
3. Existing historical TIFFs under `submission/` and `docs/downloads/` must remain clearly marked as research/audit-only. Passing a file-format test does not mean it is unique, scientifically useful, organizer-authenticated, or authorized.
4. `registry/current_status.json` and the visible website status are fail-closed but historical. Refreshing a current page should never imply the leaderboard was checked unless an as-of timestamp and source capture are stored.

## Required next steps

1. Keep the decision at **DO NOT SUBMIT**. Do not generate a synthetic/placeholder TIFF to satisfy the urgency wording; it would not pass scientific or uniqueness gates.
2. Before modeling, make the assigned method paragraph available in the project brief and explicitly record the one lane. The user asks for no human input, but the lane is a required protocol input absent from the provided material; it cannot be safely inferred.
3. Restore the complete feature stack and label/template inputs with auditable provenance; distinguish organizer-authenticated data from third-party mirrors. Restore the full registry and freeze a manifest before any uniqueness calculation.
4. For the one assigned candidate only: run feature-alone leakage canaries, fold-local whole-segment buffered hide-and-recover with exact visible masks and visible-only catalogue features, pooled DTI (`alpha=0.2`, `beta=0.8`, 300 m triangular kernel), and spatial paired 95% CI against the same-evaluator incumbent. Record the mimic and negative controls.
5. Evaluate surface uniqueness before placement and final-dot uniqueness after placement against every registry raster. Stop on the literal `|rho| > 0.90` or `>70% within 3 px` rule. Do not quietly waive the calibration rasters.
6. Validate the exact GeoTIFF against an organizer-authenticated sample and confirm finite `[0,1]` values for the entire raster. The separate selector must authorize any weekly slot; only then display a download/submit action.
7. Fix affine deprecation warnings in the shared transformation helper if appropriate. Update stale site prose and timestamped status records through the existing build path, and add a regression check for staleness.

## Official links for manual review

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem, target definition, metric, and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN survey data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)

These are official/source review pointers, not assertions that they were fetched or live-verified during this review. Internal evidence used: `registry/current_status.json`, `evidence/current_release_review.json`, `evidence/nine_site_best_files_audit.json`, `evidence/nine_site_verification_20261030.json`, `evidence/ledger_calibration_check_20261030.json`, `knowledge/10_calibration_finding_and_next_candidates_20261030.md`, and the 2026-10-30 repository review.

## Diagnostic run card (this review; no experiment)

```json
{
  "hypothesis": "No candidate hypothesis tested. The best next experimental proposal is Euler structural-index-1 solution clustering on TMI band 14, conditional on receiving the assigned lane and complete authorized feature stack.",
  "mechanism": "Clustered plausible-depth Euler N≈1 solutions may indicate buried magnetic boundaries without a mapped surface trace; untested proposal only.",
  "named_non_fault_mimic": "Magnetic dikes or mafic intrusions.",
  "holdout_dti": "NOT RUN — no candidate surface, no evaluator result, no withheld-positive count, and no 95% CI. No score estimate.",
  "correlation_overlap_vs_registry": "NOT RUN for a new surface or final dots; full registry unavailable. Existing nine-site cohort results are recorded separately and do not establish new-candidate uniqueness.",
  "raster_sha256": null,
  "validator_output": "NOT APPLICABLE — no new TIFF. Current release state remains fail-closed; no organizer-authenticated template check performed in this review.",
  "submission_name": null,
  "submission_note": "No submission: review only; no new candidate generated.",
  "verdict": "negative"
}
```
