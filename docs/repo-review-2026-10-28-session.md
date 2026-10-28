# Repository review — 2026-10-28 session

## Executive decision

**DO NOT SUBMIT.** This review did not run an experiment, create a new GeoTIFF, or use a weekly competition slot. The current historical candidate is **H-APART3-2-CTHG-DHC**, with a negative run card at [`evidence/apart3_cthg_dhc_run_card.json`](../evidence/apart3_cthg_dhc_run_card.json). It is an audit artifact only. The request's lane paragraph is absent, and the candidate has a literal all-registry uniqueness failure plus a scientific input-mapping error. A new TIFF cannot responsibly be generated within the provided constraints.

The TIF available in the repository is **not OK to upload**:

- File: [`apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif`](downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif)
- Recorded SHA-256: `9d5cab2ed8b393cd509c196961481520772bee5b1791e322e0b15cdbba696112`
- Recorded local format validator: pass against a pinned owner mirror (not an organizer-authenticated sample).
- Literal uniqueness: **99.8035%** within 3 pixels of a registered 5-px calibration-lattice raster, against a maximum permitted 70%; it also exceeds 70% overlap against two registered dense rasters (75.9043% and 72.2526%). The feature-focused prior audit reported lower overlap only after excluding these entries, which does not satisfy the literal user instruction.
- Science integrity: `IR-CTHG-BAND6-TC-02` says a radiometric Total Count band was interpreted as magnetic tilt. Do not use the claimed tilt interpretation.
- Holdout: the archived [`HOLDOUT-DTI`](../evidence/apart3_cthg_dhc_run_card.json) result is a local diagnostic, not an estimated live score. The archived CTHG primary hide-and-recover value is 0.099651 with 95% CI [0.087243, 0.111947], evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives. This is not organizer-confirmed and is not evidence that the candidate beats a 0.2778 leaderboard score.

## Nine-site comparison

The regenerated executive summary includes the nine user-specified sites, the reported best filename/score for each, and its pairwise uniqueness status. All reported live scores are labeled `OWNER-REPORT`, not organizer receipts. No new candidate's live score is estimable from the available evidence. Per-site pairwise numbers come from the archived [`evidence/nine_site_best_files_audit.json`](../evidence/nine_site_best_files_audit.json), whose source TIFFs are not currently in the checkout; the site audit could not be recomputed in this review. The underlying focus registry manifest pins source repository commits and file hashes, but that alone is not an organizer receipt or proof of current remote state.

The highest reported value in the nine-site cohort is GEMSDOE32's 0.2778 (OWNER-REPORT). Plausible reasons include a structured 37,654-pixel mask and spatial pruning, but the available evidence does not identify a causal feature or establish an attainable score improvement. The report deliberately says **not estimable** rather than mapping a holdout diagnostic to the public leaderboard.

## Three-pass review

### Pass 1 — inspect the project and its safety state

- Read README, charter, release-status logic, current candidate card, nine-site audit and portal generator.
- Found a stale positive candidate in `docs/data/latest-run-card.json` (`H-APART3-2-CSHD`, `verdict: promote`) despite negative current status. This was a release-safety bug: the landing page and machine-readable feed could disagree.
- Found that README and portal copy referred to the archived CSHD candidate as current even though `registry/current_status.json` and the CTHG card designate CTHG as the later candidate.
- Found no full cached feature stack or registry rasters under the ignored `.cache` directory. The codebase contains extensive modeling/evaluation code, but it cannot be rerun end-to-end from this checkout alone.

### Pass 2 — verify and correct the issues

- Restored the two small hash-pinned core format inputs using `scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json`. Their source is an owner-maintained GitHub mirror; hashes matched. This does not authenticate the files with the competition organizer and did not restore the feature stack or full registry.
- Updated `scripts/build_review_site.py` to source the latest negative CTHG card, keep the literal (not genuine-only) uniqueness result, build the nine-site table from pinned pairwise evidence, label score provenance, and synchronize `docs/data/latest-run-card.json` with a non-submit decision.
- Added regression tests for negative status, all nine rows, duplicate labels, source-card synchronization and deterministic portal content.
- Updated README with the standing scientific/release protocol, mandatory session-start reading, active blockers and source labels.

### Pass 3 — re-check against the request

- The rendered executive summary now says clearly that **no TIFF is OK to submit**, shows the highest owner-reported site/file/score, marks all nine prior files as not unique within this cohort, refuses to fabricate a new live score estimate, and gives an exact four-step upload process conditional on future authorization.
- The requested 3–5 hypothesis preregistration remains three hypotheses in [`next-hypotheses-20261028.md`](research/next-hypotheses-20261028.md), ranked qualitatively with layer/signature, rationale, mimic, costs/caveats. They remain proposals; no new experiment was performed because the lane is missing, and the feature stack is unavailable.
- No experiment exceeded the allowed session budget because none was run. The historical CTHG pipeline's prior development budget was not reconciled, as documented in its card; this session does not claim historical protocol compliance.
- No unique TIFF was generated. Claiming one would contradict the missing-lane requirement and absence of cached inputs. No prior TIFF has been copied as a new submission.

## Verification performed

- `python scripts/build_review_site.py`: passed; regenerated the portal and latest negative candidate feed.
- `python scripts/check_release_status.py`: passed; historical CSHD card remains negative, artifact hash matches, no slot used.
- `.venv/bin/python -m pytest -q`: **101 passed, 2 skipped** after adding portal safety tests. Initial run before restoring the sample template had 2 expected failures from the missing ignored template; after restoring the pinned template, the suite passed.
- `git diff --check`: run before final review (rerun after edits in final verification).
- `scripts/audit_nine_site_best.py`: could not be rerun because it requires every focus-site raster under `.cache/registry`; only the sample format template was restored. Existing archived pairwise results are therefore displayed as prior evidence, not newly measured results.

## Required next work

1. Obtain/confirm the actual assigned method paragraph and a fresh bounded experiment/time ledger; without that, do not start a new modeling run.
2. Restore the genuine organizer competition inputs through authorized access and restore the full feature cache plus complete registry raster set. Keep owner-mirror files clearly labeled.
3. Verify feature-band semantics from authoritative metadata and fix the shared builder centrally; clear and rebuild dependent features/models.
4. Run feature-only leakage canaries, then no more than three preregistered experiments or two hours using the specified buffered segment holdout and shared evaluator/writer.
5. Require an improved comparable HOLDOUT-DTI with paired 95% CI above zero and exact validator output, then perform surface and final-dot uniqueness against the literal full registry.
6. Keep submission-slot choice separate. Only after a selector decision should the site enable a one-click submission download; capture the organizer receipt and then update the score feed as `ORGANIZER-CONFIRMED`.
7. Resolve competition identity and score conflicts at the official DrivenData portal; prior repo links have included inconsistent competition IDs, and prompt leaderboard-high statements conflict.

## Sources

The README lists official manual-review links for DrivenData overview/problem/data, the DrivenData reference solution, USGS GeoDAWN, USGS 3DEP and INGENIOUS. This review did not claim current remote-content verification; local status claims are cited to repository evidence and checks above.
