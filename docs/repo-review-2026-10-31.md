# Repository review — 2026-10-31

**Decision: DO NOT SUBMIT.** No file in this repository is cleared for download as a competition submission or for a weekly slot. Two new GeoTIFFs were produced and validated for format, but neither clears the release gates. Their live score is not estimable.

Machine-readable gate summary: `evidence/candidates_20261031_summary.json`. Research note: `docs/research/h-s1-h-m1-results-20261031.md`. Session brief: `docs/session-prompts/2026-10-31-requirements.md`.

## 1. What was checked

| Item | Result | Evidence |
|---|---|---|
| Restored inputs | 36 pinned files restored and SHA-256 verified; owner mirrors, **not organizer-authenticated** | `scripts/restore_data.py`, `registry/data_manifest.json` |
| Official problem page | Metric (distance-weighted Tversky, α=0.2, β=0.8, 300 m triangular kernel), format (float32 GeoTIFF in [0, 1], EPSG:32611, 100 m, NaN outside allowed), single submission across rounds | [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), read via fetch tool 2026-10-31 |
| Official leaderboard | #1 xiaofanhu 0.4544; #2 cfld__ 0.3934; #3 Batik Shirt Brothers 0.3917; #4 BrandenKMurray 0.3860; #5 op01 0.3642 | [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), read 2026-10-31 (live page, not a team receipt) |
| GEMSDOE32 incumbent (owner-reported 0.2778) | Catalogue-withheld HOLDOUT-DTI 0.0045 [0.0038, 0.0053]; SGMC-calibrated HOLDOUT-DTI 0.0641 [0.0567, 0.0716] | `scripts/evaluate_holdout.py` run 2026-10-31, read-only |
| Format validator, both new candidates | PASS under strict whole-array finite check, [0, 1] range, CRS, shape, transform | `scripts/check_submission.py --strict-finite`; re-checked in `scripts/summarize_candidates_20261031.py` |
| Leakage canary (single feature, holdout AUC) | All below 0.90 (max 0.535) | run cards |
| Full-registry uniqueness, H-S1 | Surface PASS; final dots FAIL on 7 literal duplicates, all dense (3-px coverage ≥ 0.70) | `evidence/H-S1-SPECTRAL-ROLLOFF_registry_scan.json` |
| Full-registry uniqueness, H-M1 | Surface PASS; final dots FAIL on 8 literal duplicates (7 dense, 1 sparse GEMSDOE67) | `evidence/H-M1-CROSSGRAD-MG_registry_scan.json` |

## 2. Reconciling the leaderboard figures

The prompt cites 0.3195 as the current high and 0.4413 as the GEMSDOE high. Repository history shows:

- 0.4413: #1 on 2026-10-25 (`registry/leaderboard_history.jsonl`, line 3; superseded by the 2026-10-26 read).
- 0.4437: #1 on 2026-10-26 (`registry/current_status.json`).
- 0.4544: #1 on the live page read 2026-10-31 (this review).
- 0.3195: rank #2 (DARD) in the first 2026-10-04 snapshot (`registry/leaderboard_history.jsonl`, line 1). The README says rank #3, which does not match that file (IR-20261031-14). It is not on the 2026-10-31 top five.

The prompt's 0.4413 and 0.3195 are therefore historical, not current. None of these values is ORGANIZER-CONFIRMED. Confirm on your own account before any decision.

## 3. Irregularities (flagged for owner review)

- **IR-20261031-01 — Leaderboard figures disagree.** See §2. Treat the prompt values as unverified.
- **IR-20261031-02 — Submission notes state the target dot count, not the raster's count.** Both candidate notes say "37654 dots". The rasters have 40,732 (H-S1) and 36,681 (H-M1) dots after the label mask. Gate G9 records this as a failure. The note must be regenerated before any promotion.
- **IR-20261031-03 — The literal 3-px overlap rule cannot separate full-footprint rasters.** Any candidate scores about 1.0 against a raster that covers the whole footprint. In the H-S1 scan, all 7 literal duplicates had 3-px coverage ≥ 0.70. In the H-M1 scan, 7 of 8 are dense, but one sparse raster (GEMSDOE67, coverage 0.548, overlap 0.746) is a genuine literal duplicate, so H-M1 cannot be explained by the rule defect alone. The rule needs a written owner decision. Until then, it is applied as written and failures are reported as they are.
- **IR-20261031-04 — No method lane is assigned.** The checkout and prompt contain no lane paragraph. Every run is self-declared, and none can be cleared for a weekly slot.
- **IR-20261031-05 — Holdout ranking is unreliable on owner data.** On the nine owner-reported files, holdout DTI ranks in reverse of owner scores (ρ = −0.85, n = 9). Hide-and-recover gives ρ = +0.17 (CI −0.02 to +0.34, n = 117). The owner's 0.2778 cannot be reproduced from the holdout (holdout 0.0045).
- **IR-20261031-06 — Portal error cause not verified.** The error "Predicted values must be in range [0, 1]" matches files with NaN outside the footprint (GEMSDOE24, 25, 27, 28, 31 in the nine-site note). The cause has not been confirmed against the portal. The zeros variants pass the strict check.
- **IR-20261031-07 — `-nan.tif` variants sit beside the zeros candidates.** Both driver runs wrote a NaN-outside variant to `docs/downloads/`. It is not the submission candidate and has not been validated against the portal's rule. Do not use it.
- **IR-20261031-08 — Registry scope has changed since the last full scan.** The 2026-10-28 scan covered 866 manifest rows and 784 unique rasters checked (`registry/registry_uniqueness_scan_20261028.json`). The 2026-10-31 scan covers 1,204 manifest rows and 1,092 registry rasters, including 715 sibling-org rasters. The 2026-10-28 result is stale for uniqueness claims.
- **IR-20261031-09 — Two "current" status records.** `registry/current_status.json` still points to H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS. The 2026-10-31 candidates are recorded only in `evidence/candidates_20261031_summary.json`. Repointing the status requires test changes and was not done.
- **IR-20261031-10 — Restore receipt rewritten by the restore tool.** `scripts/restore_data.py` rewrote `data/restore_receipt.json`. The change was receipt-only and was reverted.
- **IR-20261031-11 — Malformed background launch.** A scan was started with a process-substitution surface (`--surface /dev/fd/63 --out /dev/null`) that did not exist as a file. It was stopped and its output was never used.
- **IR-20261031-12 — Nine-site claims re-verified this session.** `scripts/audit_nine_site_best.py` re-run: all 36 site pairs exceed the 70% within-3-px flag, and 11 pairs exceed |ρ| 0.90. A strict-format check on each site's cached copy gives 4 of 9 passing (GEMSDOE30, 32, 33, 36 pass; GEMSDOE24, 25, 27, 28, 31 fail on whole-array NaN outside the footprint, with in-footprint values in range). The earlier 2026-10-30 note agrees. The cached copies are owner-mirror bytes, not organizer-authenticated.
- **IR-20261031-14 — README rank for 0.3195 disagrees with the history file.** The README says rank #3 on 2026-10-04. `registry/leaderboard_history.jsonl` line 1 shows rank #2 (DARD, 0.3262 is #1 nchuzhoy). Repair the README text in a follow-up.
- **IR-20261031-15 — Scan gate read a missing key (fixed).** `scripts/scan_registry_uniqueness.py` read `literal_rule_passed` from the surface stage, but `audit_surface` returns `passed`. Both saved scans therefore showed the surface stage as failed when it passed (worst |ρ| 0.046 H-S1; 0.132 H-M1). The script is fixed. The two saved gate blocks were recomputed from their stored stage records, and the old values are kept as `gate_before_fix`. A full re-scan would give the same stage records. The stored gate was not otherwise changed.
- **IR-20261031-13 — Two generators write the executive-summary pages.** `scripts/build_site.py` delegates to `scripts/build_review_site.py` when the root card is not a promotion. Edit only the builder, never the HTML.

## 4. Experiments this session (budget: 3 or 2 hours)

- Experiment 1, H-S1 spectral roll-off: **negative**. SGMC-calibrated 0.0246 vs incumbent 0.0641. Literal final-dot uniqueness fails on 7 dense rasters.
- Experiment 2, H-M1 magnetic–gravity cross-gradient: **negative**. SGMC-calibrated 0.0340 vs incumbent 0.0641. Catalogue-withheld holdout 0.0304 is above the incumbent's 0.0045 (non-overlapping CIs), but the off-catalogue gate fails. Final-dot uniqueness also fails on 8 literal duplicates, one of them sparse (GEMSDOE67).
- Experiment 3 (H-B directional semivariogram): **not started**. Two of three experiments are used and the 2-hour clock has not run out. The decision to stop is about expected value, not the clock. A third candidate needs an implementation of medium cost, and the two completed candidates already miss the off-catalogue gate by 1.9× to 2.6×. The third slot is reserved for the next session.

## 5. Remaining work and limitations

1. Owner decision on the literal 3-px rule (IR-03). Without it, no candidate with non-trivial coverage can ever be cleared.
2. Assign a method lane. Without one, no weekly-slot selection is possible.
3. Verify the live portal's NaN rule against a receipt (IR-06).
4. Regenerate submission notes with the actual dot count (IR-02). Done only after a promotion decision.
5. Re-check the nine-site audit against the live submission pages (IR-12).
6. Decide whether `registry/current_status.json` should point to the 2026-10-31 candidates (IR-09).
7. Obtain organizer-authenticated inputs if available. The restored mirrors are not authenticated (IR-05 and §7 of the session brief).
8. Holdout DTI is a poor selection signal on owner data (IR-05). Treat holdout improvements as candidates for testing, not as predicted scores.
