# Repository review — 2026-10-31

## Executive decision

**No new TIF is approved for download or submission.** This review generated no candidate raster and used no competition slot. The repo's recorded GEMSDOE32 value of 0.2778 is an **OWNER-REPORT**, not an organizer-confirmed score tied to a receipt and exact raster bytes. The evidence in this checkout is insufficient to claim a new submission will exceed it, much less the current official leaderboard leader.

The highest-priority code defect found in this review was fixed: the registry surface gate treated only positive Spearman correlations above 0.90 as duplicates, although the persistent project brief requires the absolute rank-correlation threshold. A regression test now verifies that a perfect inverse-rank surface is rejected before placement.

## Three-pass review

### Pass 1 — project state and provenance

- Read the README project brief, current status registry, nine-site verification, score claims, release-gate implementation, evaluator/writer entry points, tests, and CI workflow.
- The repo already contains the requested nine-site comparison and a documented analysis of the reported GEMSDOE32 0.2778. It does **not** substantiate why that specific submission scored 0.2778 causally: the explanation that catalogue-adjacent false-positive mass was pruned is plausible and consistent with the reported nested family, but score receipts, controlled ablation, and exact organizer provenance are absent.
- The nine-site values are recorded as `OWNER-REPORT`; historical raster bytes and mirror hashes do not prove the submission-page score. The checked-in 2026-10-30 audit says all nine selected artifacts breach the pairwise 70%-within-3-pixels uniqueness rule in at least one direction. GEMSDOE25 and GEMSDOE30 are a duplicate after outside-footprint NaNs are normalized to zero. These are historical cohort findings, not a uniqueness result for a new candidate.
- The website and README already fail closed: no new artifact is authorized. Several public leaderboard snapshots and status records have different dates. Treat them as time-stamped observations, not a live 2026-10-31 leaderboard fetch.

### Pass 2 — implementation and controls

- Confirmed the shared entry points are `scripts/evaluate_holdout.py`, `scripts/submission_writer.py`, and `scripts/check_submission.py`; the release selector is distinct from these checks.
- Found and corrected the release-gate sign bug in `src/gems32/release_gate.py`: `rho > .90` became `abs(rho) > .90`, and the machine-readable rule text was corrected. Added `test_inverse_rank_surface_stops_before_placement` in `tests/test_release_gate.py`.
- Confirmed `scripts/check_release_status.py` passes after the change. It checks the repository's configured status and historical cards and confirms their hashes, fail-closed state, and no-slot status. It does not certify a newly generated submission.
- Found and corrected a stale research page that still labelled H-SEISMIC `ok_to_download`/`ok_to_submit` after its run card's positive flags had been superseded. The page now marks H-SEISMIC withdrawn and cites the failed same-evaluator holdout gate and incomplete (15-raster) uniqueness scan. The original run card remains preserved as historical evidence; its positive fields must not be interpreted as current authorization.
- Format-checked the archived GEMSDOE32 file (`docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`) using the pinned owner-mirror `sample_submission.tif`: one band, float32, EPSG:32611, 3730×3292, matching transform, and finite whole-array values in [0,1]. This proves local format compatibility only; it is not an authorized candidate and does not verify its score.
- No scientific experiment was run. The method paragraph assigning this session's single lane is not identifiable in the checkout; the complete feature stack and full registry are not restored. Running a hypothesis experiment, claiming a holdout score, or generating a purportedly unique submission would violate the run protocol or be unauditable.

### Pass 3 — clean environment and regression verification

- Created the ignored `.venv` from `requirements.txt`. A first test run had two failures because the ignored sample template was absent; restored `labels.tif` and `sample_submission.tif` with `scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json`. Their SHA-256 values matched the pinned manifest. These are owner-mirror files, not organizer-authenticated.
- Final `pytest -q -rs`: **120 passed, 2 skipped**. Both skips are `tests/test_holdout_visible_gate.py` because the local holdout data cache is incomplete; they are not passing validation evidence. Rasterio emitted 33 `PendingDeprecationWarning`s for affine multiplication.
- `scripts/check_release_status.py`: **PASS** (configured records fail closed; hashes match; no slot used).
- Strict whole-array check of the archived GEMSDOE32 TIF against the owner-mirror template: **PASS**. This is not a scientific or slot authorization.
- `python -m compileall -q src scripts tests` and `git diff --check`: **PASS**.

## Focus-site executive comparison

The score values below reproduce the supplied/repo audit, not a fresh organizer receipt. They are `OWNER-REPORT`; there is no new-score estimate. The files are not recommendations for resubmission. Refer to [`docs/research/nine-site-verification-20261030.md`](research/nine-site-verification-20261030.md) and [`evidence/nine_site_verification_20261030.json`](../evidence/nine_site_verification_20261030.json) for the raster hashes, byte-level checks, and recorded holdout diagnostics.

| Site | Best reported entry in the supplied focus list | Score evidence | Review conclusion |
|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5` | OWNER-REPORT 0.2477 | Historical only; overlaps other focus rasters. |
| GEMSDOE25 | `dotted-h19-5-d2-8` | OWNER-REPORT 0.2600 | Historical only; same prediction as GEMSDOE30 after NaN-to-zero normalization. |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5` | OWNER-REPORT 0.2449 | Historical only; overlaps other focus rasters. |
| GEMSDOE28 | `h36-1-rung30-blind-r1` | OWNER-REPORT 0.2710 | Highest item in that site's supplied list; historical only. |
| GEMSDOE30 | `d28-poisson300m-offcat-44090` | OWNER-REPORT 0.2600 | Duplicate of GEMSDOE25 under the recorded pixel comparison. |
| GEMSDOE31 | `h27-4-solo-d28` | OWNER-REPORT 0.2708 | Historical only; overlaps other focus rasters. |
| GEMSDOE32 | `h33-h33-2-b2` | OWNER-REPORT 0.2778 | Highest reported among these nine; already submitted per the supplied log, and not independently receipt-verified. Do not resubmit. |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30` | OWNER-REPORT 0.2632 | Historical only; overlaps other focus rasters. |
| GEMSDOE36 | `anderson-geothermal-pinn-38854` | OWNER-REPORT 0.2750 | Historical only; overlaps other focus rasters. |

**Score estimate for a new candidate: not estimable.** The reported 0.2778 cannot be explained or exceeded by the available holdout alone: the repo's own 2026-10-30 audit warns that its catalogue-withheld holdout ranks the nine files inversely to their owner-reported scores. The SGMC off-catalogue metric tracks this small owner-reported cohort more closely, but is still a proxy and not a validated leaderboard calibration. Do not relabel either diagnostic as a competition score.

## Main risks and irregularities

1. **Assigned lane missing.** README requires one specific method paragraph for parallel sessions, but none is identifiable here. Do not infer the lane.
2. **Data provenance/access.** The organizer data page is login-walled per repo records. Locally available core TIFFs are pinned owner mirrors; the large training feature raster / reusable full feature stack and holdout cache are absent in this checkout. An SHA match proves mirror consistency, not organizer authenticity.
3. **Full registry unavailable.** No all-registry surface and final-dot uniqueness test for a new candidate can be established from this checkout.
4. **Stale status timestamp.** `registry/current_status.json` is dated 2026-10-28 while later notes/evidence discuss 2026-10-30 events. The release check is internally consistent with its configured historical/current card but does not by itself reconcile all dated narrative claims. The status registry should be reconciled against the latest evidence before future promotion.
5. **Conflicting H-SEISMIC authorization artifacts.** Its historical run card still says `ok_to_download: true` and `ok_to_submit: true`, while README and the executive-summary page explicitly override that result because the holdout gate failed and full-registry uniqueness was not run. `docs/research/hypotheses-next-20261030.md` had repeated the stale positive claim; this review changed it to a negative/withdrawn notice. The run card remains unmodified for audit history.
6. **Incomplete holdout suite.** Two tests skip because local holdout data is incomplete. No claim about a candidate's holdout DTI is made in this review.
7. **Format-versus-spec irregularity.** The checker can enforce strict finite whole-array values; official page wording recorded in the repo allows null/NaN outside the footprint. A past portal range error is not proven to have been caused by outside-footprint NaNs. Keep a strict zeros-outside export for compatibility, but preserve the distinction between portal testing and official format evidence.
8. **Warning cleanup.** The 33 Rasterio affine deprecation warnings are non-failing but should eventually be fixed centrally and tested.

## Next steps (no slot until validation)

1. Reconcile `registry/current_status.json`, site feeds, and latest dated evidence so one explicit record owns the current state.
2. Establish the assigned lane and preregister no more than three experiments / two hours.
3. Restore the required feature stack and whole-segment spatial holdout inputs from an authenticated source where possible; record provenance and hashes. Do not treat a mirror as organizer-authenticated.
4. For each feature, run its standalone leakage canary; then fold-local buffered hide-and-recover with catalogue-derived features restricted to visible faults, exact masks, pooled DTI (α=.2, β=.8, 300 m triangular kernel), and paired spatial CIs against the incumbent.
5. Compare a candidate's surface before placement and final dots after placement against the complete registry; stop at |Spearman| > .90 or >70% directional dot overlap within 3 px.
6. Generate and validate exact saved bytes only after the science and uniqueness tests. A separate selector must authorize a weekly slot; record an organizer receipt and exact file hash afterward.
7. Keep historical negatives as useful artifacts; do not publish a download CTA or score prediction for an uncleared raster.

## Run card — review only

```json
{
  "hypothesis": "Review only; no candidate hypothesis was tested. Code defect: the surface uniqueness gate missed inverse-rank duplicates.",
  "mechanism": "A perfectly inverse-ranked raster has absolute Spearman correlation 1.0 and must trigger the specified duplicate stop before placement.",
  "named_non_fault_process_that_could_mimic_it": "A monotonic contrast inversion or sign convention change can produce a high-magnitude inverse rank correlation without representing a new geological signal.",
  "holdout_dti_and_ci": "NOT RUN for this review; local holdout cache is incomplete. No score estimate.",
  "correlation_overlap_vs_registry": "No new raster. New unit test verifies a synthetic inverse-ranked surface is rejected. No full registry comparison performed.",
  "raster_sha256": null,
  "validator_output": "No new TIF. Historical GEMSDOE32 raster passes strict local format/range validation against SHA-pinned owner-mirror template; not organizer authentication or release approval.",
  "submission_name": null,
  "submission_note": "Review only; no candidate is cleared for download or submission.",
  "verdict": "negative"
}
```

## Source pointers for manual review

These are project-recorded pointers; this review did not claim a fresh fetch of every external source.

- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData prize reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN airborne survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)
- [`docs/PROJECT_CHARTER.md`](PROJECT_CHARTER.md), [`registry/data_manifest.json`](../registry/data_manifest.json), [`registry/current_status.json`](../registry/current_status.json), and [`evidence/nine_site_verification_20261030.json`](../evidence/nine_site_verification_20261030.json)
