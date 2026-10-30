# Repository review — current session, 2026-10-30

## Executive decision

**DO NOT SUBMIT any file in this checkout.** This review generated no new GeoTIFF, ran no modeling experiment, and used no competition slot. The explicit method paragraph required by the parallel-run protocol is absent. The full feature raster, cached feature stack, and complete registry rasters are also absent, so a compliant leakage-canary, buffered hide-and-recover evaluation, and all-registry uniqueness check cannot be run. Creating a new raster without those gates would not meet the request's own validation requirements.

The current recorded candidate remains `H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS`, SHA-256 `8d90342de3a9d62bb718ea209ed5644cca0878eff906029dbc975da438cdcafd`. Its existing GeoTIFF passed a **format-only** recheck against a hash-pinned owner mirror of the sample template. This is not an organizer-authenticated template, scientific approval, uniqueness approval, or selector authorization. It is **not OK to submit**.

No experiment budget was consumed in this review. The inherited WCHD experiment record explicitly says its earlier exploratory work exceeded the stated time budget and continued after a duplicate stop; that work is retained as a negative audit record, not treated as a compliant experiment.

## Three-pass review

### Pass 1 — inventory and read the project requirements

- Read `README.md`, `docs/PROJECT_CHARTER.md`, `registry/current_status.json`, the current candidate run card, the existing nine-site audit, the holdout/evaluator and writer interfaces, release checks, and the Pages generator before deciding whether to run modeling code.
- Confirmed that the durable README brief already captures the objective, core values, scientific/evidence labels, duplicate thresholds, holdout method, experiment cap, and submit-vs-format distinction. This review updates its current-session links; the charter remains the canonical detailed protocol.
- Confirmed that the archived executive summary already has the requested nine-site table and a separately labeled “not estimable” score estimate for any new candidate. Its historical site values are `OWNER-REPORT`, not organizer-confirmed receipts.
- Found the portal's “current review” link and test-count summary hard-coded to the 2026-10-28 review even though a new review is being recorded. The current status/feed also had no current-session pointer to this review.

### Pass 2 — exercise the available checks and correct current metadata

- Created an isolated, ignored `.venv` and installed the declared `requirements.txt` dependencies. No environment or test artifacts are added to Git.
- Restored only `labels.tif` and `sample_submission.tif` from `registry/ci_format_manifest.json` into ignored `.cache/gems_data/`. Both SHA-256 values matched the manifest. The manifest explicitly identifies these as owner-maintained GitHub mirrors of login-walled competition files—not organizer-authenticated data. No training-feature raster was restored.
- Ran the full suite: **109 passed, 2 skipped, 0 failed**. Rasterio emitted 33 `PendingDeprecationWarning`s about affine multiplication; they did not fail tests.
- Ran `scripts/check_release_status.py`: **PASS**. The checker confirms the current and historical records remain fail-closed, current hashes match, portal state agrees with the candidate, and no slot is recorded as used.
- Ran `scripts/check_submission.py --strict-finite` on the current negative candidate and the separate WCHD audit artifact against the restored owner-mirror sample. Both passed structural checks: single-band `float32`, `EPSG:32611`, shape `3730 × 3292`, transform match, finite full-array values in `[0,1]`. The check verifies format/range only; it does not establish organizer acceptance, science, uniqueness, or authorization.
- Ran `git diff --check`. No whitespace errors were found before this report was added; it is rerun after the final edits.
- Updated the session-review pointer and Pages builder so the review page and machine-readable feed derive their current review path and test summary from `registry/current_status.json` instead of a fixed October 28 filename/count. After merging the companion review, the feed also synchronizes the latest verified public-board snapshot from `registry/leaderboard_history.jsonl`, preserving its observation date and explicit static-snapshot caveat; this branch did not itself fetch that page.

### Pass 3 — re-check every requested decision gate

- **Method lane:** absent. No method was inferred or implemented.
- **Feature-only leakage canaries:** not run in this review; predictor stack unavailable.
- **Holdout:** no new `HOLDOUT-DTI` measured. The imported current-candidate card contains a historical diagnostic, `HOLDOUT-DTI 0.002126` (evaluator `GEMSDOE32-HOLDOUT-v3-visible-gated`, 22,232 withheld positives, 95% CI `[0.001567, 0.002606]`). This is the card's prior measurement, not a result from this review and not a live-score estimate. No paired improvement over the incumbent is established.
- **Pre-placement surface uniqueness and final-dot uniqueness:** not re-run for the current candidate because the complete registry rasters are absent. “Off catalogue” is not evidence of uniqueness against other submissions. The current card correctly remains fail-closed.
- **WCHD audit:** its inherited run card records `99.56%` of final dots within 3 px of a registered calibration lattice, above the protocol's 70% threshold. Its saved GeoTIFF now passes the local format/range check, but it remains a duplicate-stop, post-selection, protocol-noncompliant research artifact. Do not submit it.
- **Selector and slot:** no separate selector authorization; no competition slot used.
- **Score estimate:** not estimable. Neither the historical site scores nor a holdout diagnostic supplies a validated conversion to a new leaderboard result.

## Nine-site record and score interpretation

The [executive summary](executive-summary.html) and archived audit provide the per-site filenames, reported values, and pairwise overlap results for GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36. Those historical values are owner/user reports, not organizer receipts tied to exact raster hashes. This branch did not recompute the audit during its first pass because the source rasters were not present locally. A companion 2026-10-30 review, merged from the then-current main branch, restored all nine selected TIFFs from their pinned owner-mirror commits, verified all nine hashes, and recomputed the 36-pair cohort: it reports all 36 pairs breach the directional 70%/3-pixel overlap gate in at least one direction and 11/36 also exceed |Spearman| 0.90. See [`docs/repo-review-2026-10-30.md`](repo-review-2026-10-30.md) and [`evidence/repo_review_20261030.json`](../evidence/repo_review_20261030.json). Those results describe only the selected nine files, not uniqueness against the full registry or for a new candidate.

GEMSDOE32's cited `0.2778` is likewise an **OWNER-REPORT**, not an organizer-confirmed receipt in this checkout. The recorded sequence of thinning and catalogue-collar pruning is consistent with a plausible metric mechanism: distance-kernel credit can saturate around a fault while false-positive mass continues to accrue, so removing redundant nearby dots can improve a recall-weighted DTI. But score provenance is not receipt-linked, hidden truth is unavailable, and the sequence alone cannot prove that a particular pruning step caused the reported increase or predict a better score. The detailed derivation and caveats are in [`knowledge/03_why_02778_and_the_anatomy_of_the_family.md`](../knowledge/03_why_02778_and_the_anatomy_of_the_family.md).

The prompt's `0.3195` and `0.4413` figures are historical public-leaderboard observations, not scores for these teams' files. The 2026-10-25 observation reported xiaofanhu at `0.4413`; the 2026-10-26 snapshot recorded `0.4437`. A companion review fetched the official public leaderboard on 2026-10-30 and recorded xiaofanhu at `0.4544` (date only; no time captured). Archived 2026-10-04 reads disagree whether `0.3195` ranked #2 or #3; both identify it as an early-October observation, not the current top. These public-board values are not `ORGANIZER-CONFIRMED` receipts for this project. This branch did not fetch the leaderboard itself; the static feed now uses the latest stored verified observation and must not be described as live.

## Research direction already proposed, not validated

The repository contains a ranked four-hypothesis shortlist in [`docs/research/next-hypotheses-review-20261028.md`](research/next-hypotheses-review-20261028.md). Its top qualitative test priority is a multiscale sediment-cover thickness ridge with a surface-quiescence gate, using the documented `depth_to_base_surf` and `det_elev` bands; plausible mimics include depositional facies boundaries, paleochannels, and interpolation seams. It is only a proposal: this review did not validate it or assert a numerical improvement. The other listed ideas are directional potential-field anisotropy, signed magnetic–gravity edge offset, and paired cross-front profile residual. Before any future experiment, first record the missing assigned lane, obtain the full data/cache and registry, then run leakage canaries and the shared fold-local holdout inside a fresh experiment/time budget.

## Findings, blockers, and irregularities

1. **No authorized submit file.** The only current candidate is negative; the WCHD and historical CSHD/CTHG files are audit/research artifacts. No page should present a live submit/download CTA for them.
2. **No experiment-ready inputs.** `data/` contains manifests/receipts, not `training_features.tif`; `.cache/gems_data/` contains only the two small mirror files restored for tests. The 19-band feature stack, derived cache, and full registry are missing.
3. **No method assignment.** The prompt says to use one specified method paragraph, but no such paragraph is supplied. Starting an experiment would violate the lane rule.
4. **Remote-source freshness is limited.** This branch did not fetch external pages. A companion review fetched the official public leaderboard on 2026-10-30 and its observation is now recorded in `registry/leaderboard_history.jsonl` and the static feed; it is not a live feed and says nothing about this project's submission scores. The competition data/download page remains login-gated in recorded provenance; USGS/GDR sources were not revalidated in this branch. Source URLs remain pointers, not newly verified contents.
5. **Historical archive includes withdrawn promotion copy.** `docs/research/pre-review-readme-20261028.md` retains superseded promotion language for audit history. It starts with a prominent “SUPERSEDED — DO NOT SUBMIT” warning and is not the current release decision; do not rely on its old positive claims.
6. **Remaining technical warning:** 33 Rasterio affine-operation deprecation warnings should be cleaned up in a future compatibility pass. No test currently fails because of them.

## Recommended next work

1. Provide/record the missing single method paragraph and a new bounded run budget; do not infer a lane.
2. Restore organizer-authenticated competition inputs if available, otherwise keep mirror-derived results explicitly conditional. Restore the exact cached stack and complete registry and verify their hashes/provenance.
3. Reconcile band semantics from authoritative metadata before deriving features. Run each candidate feature alone through the leakage canary.
4. Use the shared buffered whole-segment holdout/evaluator/writer with catalogue-derived features built from visible faults only and exact masking; compare paired spatial 95% CIs against the same-evaluator incumbent.
5. Apply the literal correlation and 3-px overlap stop rule to all registry rasters before placement and again to final dots. Stop on any breach.
6. Only after all scientific, uniqueness, and exact-byte format gates pass should a separate slot selector consider a candidate. Then record the organizer receipt and hash so the eventual score can be labeled `ORGANIZER-CONFIRMED`.
7. Add an authenticated/scheduled source-refresh mechanism before describing the public portal as a “current feed.” Until then, show source observation timestamps and stale-data warnings.

## Official reference links

These are manual-review links, not sources fetched during this review:

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), and [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [GDR submission 1391](https://gdr.openei.org/submissions/1391), and [EPSG:32611](https://epsg.io/32611).

## Current-review run-card pointer

The machine-readable session card is [`evidence/session_review_20261030.json`](../evidence/session_review_20261030.json). It is a negative no-experiment review; its `HOLDOUT-DTI` field is null because this review performed no holdout evaluation.
