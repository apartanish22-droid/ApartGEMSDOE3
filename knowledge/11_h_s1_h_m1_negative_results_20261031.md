# Knowledge note 11 — H-S1 and H-M1 negative results (2026-10-31)

Reusable lessons for any project on this kind of task. Numbers are HOLDOUT-DTI with 95% cluster-bootstrap CIs, from `docs/research/h-s1-h-m1-results-20261031.md`.

## What was tested

| Candidate | Signal | Catalogue holdout | SGMC off-catalogue (calibrated) | Verdict |
|---|---|---|---|---|
| H-S1 spectral roll-off | Local flatness anomaly of rtp power-spectrum slope, oriented line integrals | 0.0213 [0.0163, 0.0258] | 0.0246 [0.0181, 0.0322] | negative |
| H-M1 magnetic–gravity cross-gradient | rtp × iso_grav co-gradient alignment (H35-C form on a new layer pair) | 0.0304 [0.0243, 0.0366] | 0.0340 [0.0275, 0.0411] | negative |
| GEMSDOE32 incumbent (owner 0.2778) | — | 0.0045 [0.0038, 0.0053] | 0.0641 [0.0567, 0.0716] | reference |

## Lessons

1. **Catalogue holdout is not an off-catalogue proxy.** Both candidates beat the incumbent on the catalogue-withheld holdout and lose on the SGMC proxy. A holdout win alone is not evidence of a leaderboard gain. Always report both.
2. **Canaries are necessary but not sufficient.** Every single-feature holdout AUC stayed near 0.5 (max 0.535). That rules out a direct leakage path but says nothing about whether the candidate finds off-catalogue faults.
3. **Literal overlap rules fail on dense rasters for any candidate, and can also fail on sparse ones.** A raster that covers the whole footprint places a dot within 3 px of every footprint cell, so any candidate scores about 1.0 against it. H-S1's seven failures were all dense. H-M1 also hit one sparse raster (GEMSDOE67, 3-px coverage 0.548, overlap 0.746), a genuine literal duplicate. A coverage-normalised rule would not clear that case. Writing the rule down is an owner decision.
4. **Spectral slope magnitude is estimator output.** Steep slopes (median about −7 on real data) can be real and are not a sign of a coding error. Check with a synthetic power-law test before judging a slope estimator.
5. **Prior art check matters.** A grep found the cross-gradient functional form already in a module for another layer pair. Disclose it rather than claim novelty of the method.
6. **Check a gate's key, not just its name.** The scan gate read `literal_rule_passed` from a stage that returns `passed`, so a passing surface stage was reported as failed. Assert gate values against the stage records in a test.
7. **Note fields must come from the actual raster.** Both candidate notes said "37654 dots" when the rasters had 40,732 and 36,681. Compute the count from the raster when writing the note.

## Reusable tools

- `scripts/scan_registry_uniqueness.py` — full-registry surface and final-dot scan (sha256-deduplicated; takes about 20 minutes on 2 cores; run at most two heavy jobs at once).
- `scripts/summarize_candidates_20261031.py` — fail-closed gate summary from saved artifacts.
- `scripts/check_submission.py --strict-finite` — independent format check.

## Open questions

- Does the SGMC proxy agree with the organizer's test set? Unknown. The organizer's test set is not accessible.
- Is a per-dot attribution against SGMC traces the right test of why the proxy ranks these candidates low? Untested (see note 1).
