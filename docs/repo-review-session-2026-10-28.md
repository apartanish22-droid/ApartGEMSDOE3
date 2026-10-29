# Repository review — session pass, 2026-10-28

## Decision

**Negative / research-only / do not submit.** No new modeling experiment or competition slot was used. The existing latest candidate is available for forensic audit only. No live-score estimate is defensible from the available evidence.

## Review findings and actions

### P1 — Portal source-of-truth drift (fixed in this change)

The landing page was generated from `run_card.json` and described the historical CSHD file as the latest artifact. `registry/current_status.json` identifies the newer CTHG-DHC candidate instead. This discrepancy risked making the site's prominent download and research decision stale. `scripts/build_review_site.py` now resolves the current candidate card from the status record, checks artifact path and SHA-256 agreement, and builds the portal from that card. `scripts/build_site.py` routes its negative-state path through this current-status builder. It also refreshes `docs/data/latest-run-card.json` and `docs/assets/site-data.json`, and repairs the current-card pointer in `docs/data/feed.json`. The generated site now identifies CTHG-DHC as the latest artifact and marks it **DO NOT SUBMIT / audit only**. The scripts and `scripts/check_release_status.py` fail closed if candidate status, card, checksums, machine-readable feed, or portal disagree.

### P1 — Current CTHG candidate fails release gates (not fixed; no submission permitted)

The record `evidence/apart3_cthg_dhc_run_card.json` and `registry/current_status.json` report:

- `HOLDOUT-DTI`, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives, 95% CI: `0.099651 [0.087243, 0.111947]`. This does not prove improvement over the same-evaluation incumbent; the paired improvement interval includes zero in the card. It is not an organizer score or a leaderboard projection.
- Format check: pass for one band, finite values in `[0,1]`, CRS/shape/transform against the pinned owner-mirror template. The template is not organizer-authenticated.
- Pre-placement surface rank correlation: maximum absolute Spearman `0.212714` across 766 registry rasters checked in the card.
- Final-dot uniqueness: fail. The literal registry check records `99.8035%` within 3 px of a 5-pixel calibration lattice; two other registered dense rasters are above 70% too. The protocol provides no density or lattice exemption.
- Scientific integrity: fail. Band 6 (`tc`) was treated as magnetic tilt, while prior repository forensics identify it as radiometric Total Count (`IR-CTHG-BAND6-TC-02`). The scientific interpretation must not be promoted.
- Lane assignment is missing; overall exploratory-run accounting was not reconciled. No weekly slot was used.

Therefore the current GeoTIFF is **not authorized for upload**, despite passing file-format checks. Its exact file is linked in the generated executive summary only for audit.

### P2 — Reproduction test failures were environmental (resolved for this run)

An initial suite run could not collect tests because `pytest` was absent. After installing the declared project dependencies in an ignored virtual environment, the run reached tests but two byte-level raster tests failed because `.cache/gems_data/sample_submission.tif` was absent. Restoring the hash-pinned `sample_submission` and `labels` test inputs from the owner mirror with `scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json` resolved those setup failures. The restore receipt was returned to its tracked original after the check. Final result after reconciling the concurrent main-branch safety regressions: **101 passed, 2 skipped**. This demonstrates the tests work with the small pinned format fixture, not that the entire model pipeline was reproduced; the cached feature stack was not present.

The strict candidate check was also run against the restored template using:

```bash
.venv/bin/python scripts/check_submission.py \
  docs/downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif \
  --template .cache/gems_data/sample_submission.tif --strict-finite
```

It passed the local format/range checks. SHA-256 rechecked as `9d5cab2ed8b393cd509c196961481520772bee5b1791e322e0b15cdbba696112`. This does not alter the negative scientific/uniqueness verdict.

### P2 — README and project starting brief (updated)

The README now contains a durable summary of the user's objectives, experiment and scoring rules, the nine-site reported winners, their owner-report provenance, current fail-closed decision, and trusted starting sources. It points to the charter and current status. It deliberately does not reproduce the user's very long duplicated prompt verbatim; each session must still follow the current user instructions.

### P3 — Historical score provenance and method uncertainty (open)

The focus-site values in the table are user/site owner reports, not receipt-confirmed results. `0.2778` is the highest supplied value among the nine selected sites, but the competing `0.3195` and `0.4413` claims and present leaderboard are not established by this repository review. There is no calibrated conversion from local holdout DTI to expected live leaderboard DTI. The reported mechanism for the H33 artifact remains a hypothesis, not causal proof of its score.

## Highest supplied nine-site values

All values below are `OWNER-REPORT`, not `ORGANIZER-CONFIRMED`.

| Site | Listed top artifact | Reported value | File-use decision |
|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Study only; not authorized |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Study only; not authorized |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Study only; not authorized |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Study only; not authorized |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Study only; not authorized |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Study only; not authorized |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Highest supplied; study only; not authorized |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Study only; not authorized |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Study only; not authorized |

The exact byte checks and observed overlap metrics are archived in `evidence/nine_site_best_files_audit.json`, `evidence/nine_site_refreshed_audit_20261028.json`, and related registry records. Treat mirrored raster measurements as conditional on their stated mirror provenance.

## What needs to happen before another modeling run

1. Supply the exact assigned method paragraph/lane and start a fresh, auditable experiment/time budget. The previous candidate's three-arm cap does not grant another run.
2. Confirm the feature-band mapping from official metadata, correct the shared feature builder centrally, record a versioned receipt, and invalidate all dependent caches and results. Do not reuse the CTHG/BHGC tilt interpretation.
3. Restore and hash-check the full required feature data and registry rasters from documented sources; distinguish owner mirrors from organizer-authenticated files.
4. Propose and rank 3–5 truly distinct hypotheses before implementation. Include layer, physical signature, why it may find off-catalogue faults, prior-method comparison, expected value/cost, and required official data availability. Existing proposals are not evidence of novelty.
5. Run each feature's leakage canary, then only the pre-authorized budget of buffered, whole-segment holdout experiments using shared tools. Keep holdout DTI and any organizer receipt labels separate.
6. Verify candidate surface and final-dot overlap against every in-scope raster using the literal thresholds. Do not relax the lattice/density rule without a documented protocol change.
7. Generate a new exact-byte GeoTIFF only if the comparable holdout beats the incumbent and the scientific and uniqueness gates pass. Run strict format validation; separately require the slot selector. No present artifact meets these conditions.

## Verification record

- `scripts/check_release_status.py`: PASS (negative/fail-closed state, historical hash, no slot spent).
- `scripts/build_review_site.py`: PASS after resolving the current card from `registry/current_status.json`; generated pages contain a clear DO NOT SUBMIT notice and latest candidate.
- `scripts/check_submission.py` on CTHG-DHC against restored pinned sample, `--strict-finite`: PASS for format/range only.
- `.venv/bin/python -m pytest -q`: **98 passed, 2 skipped**.
- No new modeling experiment, candidate raster, competition upload, or weekly slot was used in this review.
