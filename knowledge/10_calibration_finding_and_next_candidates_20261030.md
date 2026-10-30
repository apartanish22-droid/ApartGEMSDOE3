# 10 · Calibration finding, what the 0.2778 result can and cannot tell us, and the next candidates (2026-10-30)

Status: **research record, no submission authorized.** Every number below carries a label:
`HOLDOUT-DTI` (evaluator version, withheld-positive count, 95% CI), `OWNER-REPORT` (copied from the supplied site list, not an organizer receipt), or `ORGANIZER-CONFIRMED` (none exists in this checkout). A projection is never written as a score.

## 1. Verified sources (checked 2026-10-30)

| What | Source | How checked |
|---|---|---|
| Problem, truth set, metric, submission format | [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Read in full (2 chunks) |
| Live leaderboard | [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Read via page fetch; shows #1 xiaofanhu 0.4544, #2 cfld__ 0.3916 |
| Data download (login-walled) | [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Not reachable without login; mirror used, hash-pinned, NOT organizer-authenticated |
| Euler deconvolution | Reid, A.B., Allsop, J.M., Granser, H., Millet, A.J., Somerton, I.W. (1990), *Magnetic interpretation in three dimensions using Euler deconvolution*, Geophysics 55, 80–91 | Confirmed in reference lists returned by web search |
| Structural index caveats | Reid, A.B. & Thurston, J.B. (2014), *The structural index in gravity and magnetic interpretation: errors, uses, and abuses*, Geophysics 79(4), J61–J66 | Confirmed in a Springer reference list |
| Cross-gradient joint inversion | Gallardo, L.A. & Meju, M.A. (2003), *Characterization of heterogeneous near-surface materials by joint 2D inversion of dc resistivity and seismic data* | **Title confirmed; journal not confirmed in this session** |
| Band names (19) | `training_features.tif` metadata, read locally after restore | Verified against the pinned SHA-256 `4371c82e…` |

## 2. What was run (experiments, budget 3 — budget now used up)

1. **Baseline on the same evaluator.** `scripts/evaluate_holdout.py` on the GEMSDOE32 incumbent (`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, SHA-256 `c55bafc4…`). Output: `evidence/holdout_incumbent_gemsdoe32_20261030.json`.
   - `HOLDOUT-DTI` (GEMSDOE32-HIDE-RECOVER-v3.0), pooled 0.004515, 95% CI [0.003816, 0.005262], withheld positives n = 22,232, 140 spatial clusters, 1,000 bootstrap reps.
   - `HOLDOUT-DTI` (GEMSDOE32-SGMC-CAL-v3.0, off-catalogue), prevalence-calibrated 0.064121, 95% CI [0.056730, 0.071649], n = 62,703.
2. **Calibration, n = 18 (superseded).** `scripts/holdout_calibration_check.py` → `evidence/holdout_calibration_check_20261030.json`. Its negative holdout correlation did not hold at scale and is withdrawn (see F1).
3. **Calibration, n = 117 (pre-registered; the decisive test).** `scripts/ledger_calibration_check.py` → `evidence/ledger_calibration_check_20261030.json`. The 117 unique live-ledger rasters (by SHA-256, from `evidence/live_ledger_rasters.json`) were fetched from their pinned refs. Every fetch matched its ledger SHA-256, so 0 were excluded. Both evaluators were run on each raster. The hypotheses and falsification rule were written in the script docstring before the run.
4. **Full-registry uniqueness of the nine focus files.** `scripts/audit_nine_site_best.py` re-run after SHA-256 fetch of the nine pinned files. It reproduced `evidence/nine_site_best_files_audit.json` byte-for-byte (no diff). Pairwise results in §3.

Budget count: item 1 (baseline) is experiment 1, item 2 (n = 18 check) is experiment 2, and item 3 (n = 117 check) is experiment 3. Item 4 is a verification re-run and is not counted. The three-experiment budget for this session is used up. No candidate raster was generated. G1 (§6) is not run; it needs a fresh budget in a later session.

## 3. Findings

**F1 · WITHDRAWN at scale. The earlier n = 18 "backwards ranking" did not hold on the pre-registered n = 117 test.**
- Pre-registered n = 117 unique live-ledger rasters (OWNER-REPORT scores), `evidence/ledger_calibration_check_20261030.json`:
  - Hide-and-recover HOLDOUT-DTI (pooled) vs owner score: Spearman ρ = **+0.1672**, p = 0.072, bootstrap 95% CI [−0.018, +0.339]. **Not significant.** The pre-registered H1a (ρ < 0 with CI below 0) is not supported. The sign is also the reverse of the n = 18 result.
  - Off-catalogue SGMC-calibrated DTI vs owner score: Spearman ρ = **+0.4042**, p = 6.2×10⁻⁶, bootstrap 95% CI [+0.221, +0.559]. **Significant and positive.** H1b is supported.
- The n = 18 result (ρ = −0.5512 holdout; +0.6877 SGMC-cal; nine-focus ρ = −0.8487 holdout, +0.9496 SGMC-cal) was a small-sample result on 18 rasters, nine of which form one family with 86.7–100% directional dot overlap. It is withdrawn.
- What survives: the off-catalogue SGMC-calibrated metric tracks the live scores moderately and significantly. The hide-and-recover holdout does not track them. The holdout is therefore not a reliable selection proxy. This is a rank statement only. It is not a score projection.
- Limitation: the owner-reported scores are a user-supplied log with no organizer receipts (OWNER-REPORT). Correlation does not establish that SGMC-CAL predicts the official score.

**F2 · The mechanism is most likely a population mismatch, not a bug (hypothesis, not proven).** Prior art: this mismatch was already recorded as `IR-32-PROXY-01` and `IR-32-PROXY-02` in `registry/irregularities.json`, and in [knowledge/06](06_live_ledger_inversion_and_the_uniqueness_ceiling_2026-10-26.md) ("catalogue-based holdouts measure a different population"; catalogue-proximal depletion of hidden truth at 0.01–0.07× within 1–2 px). This session adds a quantitative rank test on owner-reported scores. It does not discover the mismatch.
- Official truth set: "expert-labeled new faults … not contained within the current public USGS database" ([problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)).
- Hide-and-recover scores recovery of *withheld catalogue* segments. The submission writer masks every catalogue cell (`scripts/submission_writer.py` → `& ~labels`). A file tuned for new faults is therefore penalised on the catalogue population by construction.
- Falsification test (partial): the SGMC-calibrated off-catalogue proxy shows a positive, significant rank relation with live scores (n = 117, ρ = +0.40). This is consistent with the population-mismatch explanation for the holdout, but does not prove it. A proxy that is *not* the SGMC map has not been tested, so the test is incomplete.

**F3 · Why GEMSDOE32 (0.2778) sits at the top among the focus files: what can and cannot be said.**
- Owner-reported order of the top two: GEMSDOE32 0.2778, GEMSDOE36 0.2750. Both are the two highest on the SGMC-calibrated proxy: GEMSDOE36 0.064444 [0.057087, 0.071958], GEMSDOE32 0.064121 [0.056730, 0.071649] (`HOLDOUT-DTI`, SGMC-CAL-v3.0). The proxy reproduces the *top-two set* but not the exact order; the 0.00032 gap is far inside the CI.
- GEMSDOE32 has the **lowest** hide-and-recover DTI among the nine (0.004515), so the catalogue holdout cannot explain its score. Consistent with the pruning narrative in [knowledge/03](03_why_02778_and_the_anatomy_of_the_family.md), but causation is not established. No organizer receipt ties the 0.2778 to these bytes.
- Uniqueness: GEMSDOE32 overlaps GEMSDOE36 (1.0000 of GEMSDOE32 dots within 3 px of GEMSDOE36, Spearman 0.9843), so it is **not unique** against the nine.

**F4 · Uniqueness of the nine focus files (verified, `evidence/nine_site_best_files_audit.json`).**
- Across all 36 pairs, the larger of the two directional overlaps is at least 97.31% (minimum: GEMSDOE28↔GEMSDOE36). The smallest single directional value is 86.72% (GEMSDOE27 dots within 3 px of GEMSDOE32). Maximum Spearman of any pair: 1.0000 (GEMSDOE25 vs GEMSDOE30, identical surfaces by rank).
- Result: none of the nine files is unique against the others. Duplicate gate fails for all nine.

**F5 · Leaderboard references in the prompt are stale.** See IR-APART3-20261030-03 in `registry/irregularities.json`. Live page on 2026-10-30: #1 0.4544. The 0.3195 figure is rank #3 on the 2026-10-04 snapshot.

**F6 · External data is not the bottleneck; validation alignment is.** Each external layer I searched for is referenced by at least one module in `src/gems32/` (grep: the 2 m temperature probes appear in `hypotheses33.py` and `trhv.py`; `derived_sgmc` in 7 files; `depth_to_base_surf` in at least four modules: `bhgc.py`, `fbgr.py`, `h33.py`, `h35_new.py`). Grep shows references, not how each module uses them. Adding layers without a valid target would repeat the same failure.

## 4. Irregularities flagged for review

- **IR-APART3-20261030-01 (high):** the mirror's `existing_faults.tif` is byte-identical to `labels.tif`. The holdout evaluator reads only `labels.tif`, so the numbers above are unaffected. Do not build catalogue features from the mirror's `existing_faults.tif`.
- **IR-APART3-20261030-02 (high, revised):** the primary promotion gate (hide-and-recover HOLDOUT-DTI win) is not a significant predictor of live scores (n = 117, ρ = +0.17, CI spans 0). The n = 18 claim of a backwards ranking is withdrawn. This session did **not** change the gate. Changing it is an owner decision. Extends the prior flags IR-32-PROXY-01 and IR-32-PROXY-02.
- **IR-APART3-20261030-05 (medium):** `knowledge/06` refers to `scripts/fetch_live_ledger_rasters.py`, which is not in the repository. The fetch-and-verify step was done by `scripts/ledger_calibration_check.py`.
- **IR-APART3-20261030-03 (medium):** stale leaderboard figures in the prompt.
- **IR-APART3-20261030-04 (low, fixed):** `restore_data.py` overwrote the receipt. Fixed with a regression test.

## 5. Candidate hypotheses (ranked by expected decision value and cost)

Expected DTI improvement is **not estimable**. Ranks are qualitative judgment, and none has been validated.

| Rank | Candidate | Layers (band numbers from `training_features.tif`) | Physical signature | Why it could find a fault missing from the catalogue | How it differs from existing code | Named non-fault mimic | Cost | Status |
|---|---|---|---|---|---|---|---|---|
| 0 (do first) | **V1 · Validation realignment.** Use SGMC-calibrated off-catalogue DTI as the primary ranking metric; keep hide-and-recover as a secondary diagnostic. | none (existing evaluator) | n/a | Scores the population the official truth set is drawn from (F2) | Changes which metric gates promotion; `holdout.py` unchanged | SGMC map is a proxy, not expert labels | ~0 compute | **Supported by the n = 117 test (ρ = +0.40, CI [+0.22, +0.56]).** Gate change still needs an owner decision. |
| 1 | **G1 · Euler deconvolution with structural index 1 (faults), depth 0.4–6 km.** Solve the Euler homogeneity equation on TMI (band 14) with a sliding window; keep clustered solutions aligned along a trend. | 14 `tmi` (derivatives computed from the grid, not the band-6 tilt) | Clusters of N≈1 solutions aligned in a trend (contact-like N≈0 is excluded) | Buried magnetic contrasts with no surface trace can give aligned depth solutions | `tmspi.py` uses Euler N≈0 contacts (grep: "Euler structural index N ≈ 0"). A grep found no N≈1 solver in `src/` or `scripts/`. This is a grep result, not a full code review. | Magnetic dikes and mafic intrusions also have N≈1 (Reid et al. 1990; Reid & Thurston 2014) | Medium | **Top candidate.** Preregistration in §6. |
| 2 | **G2 · Gravity–magnetic cross-gradient coupling.** Joint structure measure from iso-gravity (band 13) and TMI or RTP (bands 14, 2) gradients, in the sense of Gallardo & Meju (2003). | 13 `iso_grav_anom`, 14 `tmi`, 2 `rtp` | High gradient magnitude where the two fields' gradients are collinear and co-located | A shared edge in two independent fields suggests a structural boundary even without a surface trace | Partly overlaps `h35_new.py`, which uses a gradient-product × cosine alignment on `cond_surf` (17) and `depth_to_base_surf` (15). The layer pair and physics differ. Novelty must be checked against `h35_new.py` before running. | Lithological contacts without faulting | Low–medium | Queued after G1. |
| 3 | **G3 · 2 m shallow-temperature probes as an independent validation axis, not a feature.** | GDR 1391 probe layer (restored, hash-pinned in `registry/data_manifest.json`) | Probe anomalies as a test of candidate dots | Using them as validation avoids leakage into the candidate | `trhv.py` and `hypotheses33.py` reference the probes (grep). Whether they use them as features was not checked in this session. Use as a held-out test is not found in the grep results. | Shallow groundwater flow, sinter and alteration unrelated to faults | Low | Diagnostic only. |

Not proposed: basement-step (`depth_to_base_surf`), radon, chi/knickpoint, tilt-phase and phase congruency, lineament density, ridge concordance, Laplace gravity. Each is already implemented somewhere in `src/gems32/` or `src/gemsdoe32/`.

## 6. Preregistration for G1 (not run)

- **Hypothesis:** N≈1 Euler solutions that cluster along a trend in the 0.4–6 km band mark buried faults with no catalogue trace.
- **Data:** `training_features.tif` band 14 (`tmi`), 100 m grid, EPSG:32611, shape 3730 × 3292, nodata −3.4028e38. Handle nodata before differentiating.
- **Method:** Euler's homogeneity equation with N = 1. Solve for source position (x, y, z) in sliding windows. Compute x and y derivatives numerically from the grid. Keep solutions with depth 0.4–6 km and low residual. Build a density surface of solutions and threshold it to dots.
- **Leakage canary (required first):** the G1 surface alone on `HOLDOUT-DTI` (hide-and-recover) and SGMC-CAL. AUC above 0.90 means leakage until disproven.
- **Primary metric:** SGMC-CAL off-catalogue DTI with paired spatial bootstrap against the GEMSDOE32 incumbent (0.064121 [0.056730, 0.071649]).
- **Uniqueness:** literal full-registry test (451 rasters restore to about 375 MB; not yet restored) plus the nine-site audit. Surface Spearman ≤ 0.90 and ≤ 70% of dots within 3 px.
- **Stop rules:** three experiments or two hours per session. A negative result is a deliverable. This session's budget is used up; G1 runs in a later session.
- **Mimic check:** report the share of solutions on mapped dikes or intrusions, if a free official source is found. This is not yet verified.

## 7. Limitations and access still needed

- DrivenData data page is login-walled. Organizer copies of `training_features.tif`, `labels.tif`, and `existing_faults.tif` are not verified; mirrors are integrity-pinned only.
- No organizer score receipt for any raster. Every score in the repo is `OWNER-REPORT`.
- The full 451-raster registry is not restored locally, so the literal all-registry uniqueness gate has not been run for any new candidate.
- Mineral-occurrence or dike-map sources for the G1 mimic check are not yet identified. Candidates: USGS mineral-resource and dike databases. Each needs an access check before use.
