# Pre-registration: E1 — Euler structural-index-1 solution density on TMI (2026-10-31)

Written before any candidate raster was computed in this session. Labels: HOLDOUT-DTI, OWNER-REPORT, ORGANIZER-CONFIRMED.

## 1. Hypothesis
Clusters of plausible-depth Euler N = 1 solutions computed on the total magnetic intensity field (training_features band 14, `tmi`) mark buried magnetic boundaries (fault-controlled contacts, dikes, or intrusion margins) that have no surface trace in the USGS/INGENIOUS catalogue. Dots placed at the highest solution density should be a new family, not a re-pruning of the GEMSDOE32 family.

## 2. Layer and signature
- Layer: band 14 `tmi` (training_features.tif, 1-based). Derivatives: x, y by central differences; z by FFT (|k| filter), z positive downward.
- Signature: Euler N = 1 solutions (x0, y0, z0, B) in 15 x 15 px windows (1.5 km), window step 2 px. Accept a solution if 2 px <= z0 <= 30 px (200 m – 3 km) and (x0, y0) lies inside its window.
- Output: Gaussian (sigma 2 px) smoothed solution count, restricted to the valid footprint. Dots = top 37,654 cells (the same dot budget as the GEMSDOE32 champion, so the comparison is not a budget artifact).

## 3. Why this might find a fault missing from the catalogue
Euler N = 1 is the structural index of a point/line-like magnetic source at a depth, and the depth window excludes near-surface cultural and geologic noise. A cluster at depth without a catalogue trace is the target. Only band 14 is used. No catalogue layer (labels, existing_faults, SGMC, Qfaults, distance-to-known-fault) is read by feature construction.

## 4. How it differs from what is in the repo
- `src/gems32/tmspi.py` uses TDR zero-crossings and Thurston–Smith local wavenumber with an N ≈ 0 contact model on bands 3, 5, 9, 11. It does not compute N = 1 windowed solutions on band 14.
- Repo search found no N = 1 Euler implementation in `src/`. This is a targeted search, not proof of absence.

## 5. Named non-fault mimic
Magnetic dikes, mafic intrusions, and magnetic basement lithology boundaries produce the same N = 1 solution clusters.

## 6. Pass / fail gates (all automated, fixed now)
1. Method canary: synthetic 1/r point-source field (homogeneous degree -1, exact N = 1) must recover the true source depth within 1 px and the true x/y within 2 px. If not, the implementation is wrong and the experiment stops.
2. Leakage canary: AUC of the density feature alone vs the catalogue labels must be <= 0.90 (repo rule). Above 0.90 is treated as leakage until proven otherwise.
3. Format: `scripts/check_submission.py --strict-finite` against the restored template, with values binary {0, 1}, zero outside the footprint, no NaN.
4. Holdout: `scripts/evaluate_holdout.py` (HIDE-RECOVER v3.0 and SGMC-CAL v3.0). Note: GEMSDOE32 champion HIDE-RECOVER = 0.0045 (HOLDOUT-DTI), random dots in the footprint = 0.045 (control run this session). The HIDE-RECOVER gate is therefore not a discriminating test; SGMC-CAL is the one correlated with live scores (rho +0.40, n = 117, OWNER-REPORT).
5. Non-regression: SGMC-CAL must not be below the champion (0.0641, HOLDOUT-DTI, GEMSDOE32-SGMC-CAL-v3.0). Random control = 0.0468.
6. Uniqueness: Spearman <= 0.90 AND <= 70% of dots within 3 px vs each of the nine focus rasters and the 117 ledger rasters (`evidence/live_ledger_rasters.json`, SHA-verified).

## 7. Budget
Experiment 1 of at most 3 this session, and the 2-hour lane limit. Promotion is a separate selector step and is not implied by passing gates.

## 8. Expected outcome (stated before the run)
Negative is the most likely result. A depth-filtered Euler density is not expected to match the SGMC-CAL level of the champion without the catalogue-based pruning the champion uses. A pass on gates 1–3 with a fail on gate 5 is recorded as negative.
