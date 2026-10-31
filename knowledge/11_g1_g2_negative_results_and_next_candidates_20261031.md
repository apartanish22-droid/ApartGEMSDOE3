# 11. G1 and G2 negative results, instrument controls, and next candidates (2026-10-31)

Status: **research record. No file is cleared to download or submit.** All numbers are HOLDOUT-DTI from the shared evaluator unless labelled otherwise. No organizer receipt was obtained, and no leaderboard score is projected.

## 1. What was done (3 experiments, budget reached)

| # | Experiment | Result | Verdict |
|---|---|---|---|
| 1 | **G1** Euler deconvolution, structural index N = 1, on TMI (band 14). Pre-registered in note 10 §6. | Canary AUC 0.512 (per-cell 0.44–0.57). Holdout DTI 0.004822 [0.003858, 0.005924]. Primary SGMC-CAL DTI 0.03977 [0.03392, 0.04547] vs incumbent 0.06412 [0.05673, 0.07165]. | **Negative.** Worse on the primary metric, and no ranking signal. |
| 2 | **G2** Gravity–magnetic gradient coupling (bands 13 and 14). Pre-registered in note 10 §5. | Canary AUC 0.508 (per-cell 0.46–0.56). Holdout DTI 0.004722 [0.003265, 0.005900]. SGMC-CAL DTI 0.03217. | **Negative.** Same as G1. |
| 3 | **Instrument controls** for the canary. | Oracle surface built from withheld truth: AUC 1.000. Uniform noise: AUC 0.500. | Instrument valid. The G1 and G2 null results are real and not a broken test. |

Evidence: `evidence/SESSION_20261031_RUN_CARD.json` (consolidated card), `evidence/H-G1-EULER-N1-TMI_20261031T044935Z_run_card.json`, `evidence/H-G2-GRAV-MAG-COUPLING_dry_run_20261031.json`, `evidence/G-CANARY-CONTROLS_experiment3.json`, `evidence/G1_shared_evaluator_20261031.json`, `evidence/incumbent_shared_evaluator_20261031.json`.

## 2. Paired comparison with the incumbent (GEMSDOE32, 0.2778)

Both files were scored through the same shared evaluator (`scripts/evaluate_holdout.py`):

- HOLDOUT-DTI pooled: G1 0.004822 vs incumbent 0.004515. The intervals overlap.
- Per-cell paired (8 cells): G1 beats the incumbent in 3 of 8. Mean paired difference +0.00007, cell-bootstrap 95% CI [−0.00104, +0.00119]. **The CI spans zero, so there is no paired win.**
- SGMC-CAL (the pre-registered primary metric, supported by the n = 117 calibration test in note 10): G1 is lower, with non-overlapping CIs.

## 3. Uniqueness (literal gates, 451 focus-registry rasters)

- Surface |Spearman|: max 0.091 (limit 0.90). Passes.
- Final dots within 3 px, excluding the calibration lattice: max 0.389 (limit 0.70). Passes.
- The calibration lattice `GEMSDOE24/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` gives 1.000 for G1 and 0.981 for G2. **This fails the literal rule.**
- Control: 37,284 uniformly random dots score 0.9982–0.9989 against the same lattice. The lattice cannot distinguish any candidate. The repo already records this in IR-42-UNIQ-01 (`registry/current_status.json`). The literal rule is therefore a rule defect and needs an owner decision. This session did not exempt the lattice.
- Two registry rasters could not be measured (GEMSDOE31 non-finite inside footprint; GEMSDOE36 grid mismatch). The audit is incomplete by two files.

## 4. The file that was generated (labelled, not cleared)

`docs/downloads/gemsdoe32-NEG-DO-NOT-SUBMIT-g1-euler-n1-tmi-20261031T044935Z-f1362e88-zeros.tif`
- SHA-256 `c4384fe6f656eb9351607a5b8d2a0ea36f3668ec65b560a7f34d2f086cf70f8a`
- Submission name: `NEG-DO-NOT-SUBMIT-g1-euler-n1-tmi`. Note: `NEG DO-NOT-SUBMIT G1 Euler N=1 TMI dots: canary AUC 0.51 (no signal), literal lattice rule fails` (96 characters).
- Validator: `scripts/check_submission.py --strict-finite` passes all 7 checks. An independent check also confirms float32, EPSG:32611, 3730 × 3292, a transform equal to the template, no NaN, values in {0, 1}, 37,284 positive cells, none outside the footprint.
- The NaN-outside sibling file that the writer also produced was deleted, because it fails the strict check and could be downloaded by mistake.

## 5. Answers to the questions in the brief

- **Why 0.2778 scored highest among the nine sites:** see [note 03](03_why_02778_and_the_anatomy_of_the_family.md). Nothing in this session changes that analysis. The owner-reported score is not an organizer receipt.
- **Can we beat 0.2778?** Not established. No candidate in this session passed the holdout gate, and the organizer's score for any new file cannot be obtained from this sandbox. The estimate for a new file is **not estimable**.
- **Is the portal error caused by NaN outside the footprint?** Unverified. The competition template `sample_submission.tif` itself contains NaN outside its footprint: 7,111,787 of 12,279,160 cells. The official reference solution (GitHub repo `drivendataorg/gems-prize-reference-solution`, notebook cells 12, 16, 19) writes sigmoid outputs into a zero-initialised `np.zeros` array (float64 by default) and saves it with no nodata value. The reference therefore has no NaN anywhere. (Dtype was checked in the notebook source, not by running it.) So a finite, zero-filled [0, 1] file is consistent with the reference, but the cause of the error message is not confirmed.

## 6. Irregularities (for review)

1. **IR-S-01** The G2 pre-registration describes a signal "high where gradients are collinear" but names the cross-gradient, which is zero for collinear gradients. Implemented as min(normalised magnitudes) × (1 − sin θ), which is the collinearity reading. Owner should confirm.
2. **IR-S-02** The literal 3-px uniqueness rule cannot be satisfied by any dot set against the calibration lattice (random dots 0.998–0.999). Owner decision required.
3. **IR-S-03** The uniqueness audit is incomplete (2 of 451 rasters unmeasurable).
4. **IR-S-04** The repo's "NaN-free whole array" gate is stricter than the competition template, which contains NaN outside its footprint.
5. **IR-S-05** The reference notebook reads `numeric_features.tif`. This repo uses `training_features.tif`. Naming and content equivalence are unverified.
6. **IR-S-06** The organizer, problem, NLR, epsg.io, and GitHub Pages hosts were unreachable from this sandbox (HTTP 000). Only GitHub, PyPI, and npm were reachable. The leaderboard values in the brief (0.4413, 0.3195) were not re-read live.
7. **IR-S-07** Two pytest failures seen before restoring data were environmental. All tests pass after `scripts/restore_data.py --group all`.
8. **IR-S-09** G1 did not run the structural-index plateau test (see §7). SI = 1 was pre-registered, not verified. A wrong SI is a possible cause of the null result.

## 7. Method lesson from G1 (why the next candidate changes)

Euler deconvolution depends on the integer structural index. Reid & Thurston (2014) and the Euler literature require the depth solutions to form a plateau across window sizes when the index is right. When the index is wrong, depth estimates do not plateau. This is supported by the SBGf base-level paper that cites Reid et al. (2014) and Reid & Thurston (2014) (`https://sbgf.org.br/mysbgf/eventos/expanded_abstracts/15th_CISBGf/Correct%20structural%20index%20defined%20by%20base%20level%20estimates%20in%20Euler%20deconvolution%20.pdf`). G1 used N = 1 without that check, so the null result cannot distinguish "no buried faults in TMI" from "wrong structural index".

References (verified in this session): Reid, Allsop, Granser, Millett & Somerton (1990), *Geophysics* 55, 80–91, doi:10.1190/1.1442774. Gallardo & Meju (2003), *Geophys. Res. Lett.* 30(13), 1658, doi:10.1029/2003GL017370. Reid & Thurston (2014), title verified via citing papers; journal details not independently checked.

## 8. Candidate hypotheses for the next session (3–5, ranked, none run)

Each candidate passes the canary before any holdout or uniqueness work. None is authorised for a slot.

| Rank | Candidate | Layers (`training_features.tif` band numbers) | Physical signature | Why it could find an uncatalogued fault | How it differs from existing code | Named non-fault mimic | Cost | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | **H1 · Euler with plateau-verified structural index.** Test N = 0, 1, 2 on the same TMI windows and keep only solutions from the index whose depth estimates plateau across window sizes (for example 15, 21, 31 px). | 14 `tmi` | Depth plateau at the correct integer index; cluster of solutions at 0.4–6 km | Fixes the gap that sank G1. Only solutions with a verified index enter the surface. | G1 (`src/gems32/euler_n1.py`) is the only N = 1 solver. `tmspi.py` uses N ≈ 0 contacts. | Magnetic dikes and intrusions also have N = 1 plateaus | Medium | Next. Requires a synthetic plateau test before real data. |
| 2 | **H2 · G2 with RTP instead of TMI.** Band 2 `rtp` removes inclination effects, so its gradient alignment with gravity should be more meaningful. | 13 `iso_grav_anom`, 2 `rtp` | Same coupling as G2, on RTP | Tests whether G2 failed because TMI gradients are skewed by inclination | Same code (`cross_grad_g2.py`), different band. Overlap with `h35_new.py` must be checked first (layers 17 and 15 there). | Lithological contacts without faulting | Low | Queued after H1. |
| 3 | **H3 · 2 m shallow-temperature probes as an independent validation axis** (not a feature). | GDR 1391 probe layer (hash-pinned in `registry/data_manifest.json`) | Probe anomalies as a test of candidate dots | Uses the probes only for validation, so there is no leakage | `trhv.py` and `hypotheses33.py` reference the probes. Whether they are used as features was not checked. | Shallow groundwater flow, sinter, alteration | Low | Diagnostic only. |
| 4 | **H4 · Euler depth-gated coupling.** Use the H1 solution depths to keep only the gravity–magnetic coupling from shallow sources (<2 km). | 13, 14, plus H1 depths | Shallow co-located gradient alignment | Targets the zone where faults are most likely to show in both fields | Combines H1 and G2; no existing code. | Shallow intrusions and lithologic contacts | Medium | Only after H1 passes. |

Not proposed (already implemented in `src/`): basement step, radon, chi/knickpoint, tilt-phase and phase congruency, lineament density, ridge concordance, Laplace gravity.

## 9. Limits and what is needed

- **Organizer access:** the data page and leaderboard need login or are unreachable from here. A real score cannot be obtained without it.
- **Uniqueness rule:** the owner must decide whether the literal lattice rule is intended. The repo's null-calibrated excess (`registry_audit.space_filling_coverage`) is the candidate fix.
- **Template NaN:** confirm with the organizer whether NaN outside the footprint is accepted. Zero-filled output is safe either way.
- **Free external data:** no new free external source was found in this session that is both reachable and not already restored.
