# Session review — 2026-10-31: E1 Euler N=1 experiment, verification, and the submission decision

**Verdict: NO FILE IS CLEARED TO DOWNLOAD OR SUBMIT.** E1 (`E1-EULER-N1-TMI-37654`) is a negative result. The highest-scoring file, GEMSDOE32 zeros (0.2778, OWNER-REPORT), is already submitted, and every other focus file is in the same overlapping family.

Labels used: **HOLDOUT-DTI** (evaluator version, withheld positives, 95% CI) · **OWNER-REPORT** (copied from the prompt or repo history; no organizer receipt) · **MEASURED-FROM-BYTES** (computed here from a named file) · **PUBLIC-LEADERBOARD-OBSERVATION** · **PROJECTION** (never a score).

Summary page: [executive summary, decision section](../executive-summary.html). Run card: [`evidence/euler_n1_E1_run_card.json`](../../evidence/euler_n1_E1_run_card.json).

## 1. What was done (in order)

| Step | Action | Result |
|---|---|---|
| 1 | Read README, PROJECT_BRIEF, 2026-10-31 reviews, release gate, evaluator | Fail-closed policy confirmed; no file cleared at start of session. |
| 2 | Checked network reachability (curl) | Reachable: github.com, codeload, api.github.com, pypi. **Unreachable (HTTP 000):** drivendata.org, docs.nlr.gov, usgs.gov, epsg.io, buffedlizard55-lab.github.io. |
| 3 | Cloned the official GEMS reference solution | `github.com/drivendataorg/gems-prize-reference-solution`, single commit `aebe92f`. Read the notebook (see §3). |
| 4 | `pip install -r requirements.txt` in `.venv`; `scripts/restore_data.py --group all` | 36 files restored and SHA-256 verified in about 70 s (owner mirrors, not organizer-authenticated). |
| 5 | `pytest -q` | 121 passed before E1; 125 passed after E1 canary tests were added. |
| 6 | Format/range scan of 31 downloadable and scored TIFs | All finite values in [0,1]. NaN in 18 files; in every case the NaN count equals the 7,111,787 outside-footprint pixels, so none is inside the footprint. See §4. |
| 7 | Holdout instrument control: 2 random 37,654-dot rasters | Random HIDE-RECOVER 0.0452 and 0.0489; SGMC-CAL 0.0468 and 0.0462. See §5. |
| 8 | Champion mechanism check from bytes | Champion = d2.8 minus 6,436 dots within 2 px of `labels.tif`. See §6. |
| 9 | Pre-registered E1 (Euler N=1 on TMI band 14) | [Pre-registration](preregistration-euler-n1-tmi-20261031.md), written before any candidate. |
| 10 | Implemented `src/gems32/euler_n1.py` with method canary `tests/test_euler_n1.py` | Canary found and fixed a test-metric problem (far-field edge artifacts), not a sign error. 4/4 pass. |
| 11 | Ran E1 once (`scripts/run_euler_n1_experiment.py`) | 450,002 accepted solutions, 37,654 dots, deterministic (SHA reproduced on rerun). |
| 12 | Gates: format, leakage canary, holdout, SGMC non-regression, uniqueness | See §7. E1 fails the SGMC non-regression gate and the literal uniqueness rule. |

Experiments used: **1 of 3** (budget). No weekly submission slot was used.

## 2. Candidate hypotheses considered (ranked by cost and gate fit)

The prompt asked for 3–5 candidates before implementation. The repo already holds a shortlist (see `docs/repo-review-2026-10-31.md`). The list below reuses it, adds the verified constraints, and does not add untested claims.

| Rank | Candidate | Layers | Signature | Why it might find an uncatalogued fault | Difference from repo code | Cost | Status |
|---|---|---|---|---|---|---|---|
| 1 | Euler N=1 solution density | band 14 `tmi` | windowed N=1 solutions at 0.2–3 km depth | buried magnetic boundary without a surface trace | `tmspi.py` is N≈0 contact on bands 3/5/9/11 | medium | **Run (E1): negative** |
| 2 | Gravity–magnetic cross-gradient coupling | bands 13 `iso_grav_anom`, 14 `tmi`, 2 `rtp` | co-located, concordant gradients | shared basement boundary under cover | `h35_new.py` has multi-domain pairing; equivalence not checked | low–medium | not run |
| 3 | Directional residual semivariogram | bands 2, 13 | along- vs cross-strike texture after fold-local trend removal | fractured, offset basement corridors | no direct semivariogram residual statistic found in search | medium | not run |
| 4 | Signed cross-edge offset persistence | bands 2, 13, 18 | recurring edge-normal offsets | faulted contacts at different depths | joint-field features exist; precise statistic not verified absent | high | not run |

Ranking by expected DTI improvement is **not estimable**: no candidate has a measured lift. Ranking is by implementation cost and by how cleanly the candidate differs from the repo.

## 3. Official reference (verified from the cloned repository)

Source: `github.com/drivendataorg/gems-prize-reference-solution`, commit `aebe92f` (see the repo's `unet-mc-cv-reference-solution.ipynb`).

- Inputs: `data/numeric_features.tif` (features) and `data/labels.tif` (labels).
- Label binarization: `y_orig[y_orig < 1] = 0`, so positive class = value 1 in `labels.tif`.
- Output: written with the CRS and transform of `labels.tif`; the notebook notes that thresholding the map "may be advantageous for better scoring".
- The notebook does **not** contain the metric (DTI) or a validator. It also does not say how NaN is handled in the output. The NaN rule therefore still rests on the owner-mirrored template and an unverified statement.
- Interpretation (repo-verified, not organizer-confirmed): the organizer labels that the model trains on are the same catalogue used for `labels.tif` in this repo, which fits the premise that the hidden test is a different set of faults.

## 4. Portal error: "Predicted values must be in range [0, 1]"

Measured from bytes (31 files):
- Every finite value is in [0, 1]. No infinite values.
- NaN in 18 files. In every case the NaN count equals the 7,111,787 pixels outside the footprint, so none is inside.
- The owner-mirrored template `.cache/gems_data/sample_submission.tif` has nodata = NaN and the same 7,111,787 NaN pixels outside its 5,167,373-pixel footprint.

Conclusion: NaN outside the footprint is the template's own pattern. The file contents do not explain a range error. Whether the portal rejects NaN is **unverified**. Owner-reported scores exist for NaN files (0.2708, 0.2600, 0.2477), which suggests the portal accepted some of them. Action: obtain the exact failing file name and portal text from the user, and the organizer statement on NaN.

## 5. Instrument controls (null baselines)

[`evidence/random_dot_controls_20261031.json`](../../evidence/random_dot_controls_20261031.json). Random uniform 37,654 footprint cells, `numpy.random.default_rng(0|1)`.

| Dots | HIDE-RECOVER HOLDOUT-DTI (v3.0) | SGMC-CAL HOLDOUT-DTI (v3.0) |
|---|---|---|
| Random seed 0 | 0.04517, CI [0.0409, 0.0495], n=22,232 | 0.04678, n=62,703 |
| Random seed 1 | 0.04890, CI [0.0442, 0.0530], n=22,232 | 0.04616, n=62,703 |
| GEMSDOE32 champion | 0.00452, CI [0.0038, 0.0053], n=22,232 | 0.0641, CI [0.0567, 0.0716], n=62,703 |

Reading: random placement beats the champion by about 10× on HIDE-RECOVER. The HIDE-RECOVER metric therefore rewards dots near catalogue-type withheld faults and penalises pruning away from the catalogue. This is an instrument property, not a bug in the evaluator (the evaluator reproduces the recorded values exactly). **Flag IR-4.**

## 6. Champion mechanism, verified from bytes

[`evidence/champion_catalogue_proximity_20261031.json`](../../evidence/champion_catalogue_proximity_20261031.json). Distances from `labels.tif` (60,988 positive pixels; `existing_faults.tif` has identical positives).

| File | Dots | Within 2 px (200 m) of catalogue | Within 300 m | Beyond 1 km |
|---|---|---|---|---|
| H19-5 parent (nan) | 121,131 | 14.3% | 19.95% | 58.9% |
| GEMSDOE24 d1.5 (nan) | 60,069 | 14.6% | 19.9% | 59.3% |
| GEMSDOE25 d2.8 (nan) | 44,090 | 14.6% | 19.5% | 59.6% |
| **GEMSDOE32 champion** | **37,654** | **0.0%** | **5.8%** | **69.8%** |
| E1 Euler N=1 (this session) | 37,654 | 7.8% | 11.0% | 71.2% |

- All 37,654 champion dots lie inside d2.8. The champion = d2.8 minus 6,436 dots.
- 6,436 total within 2 px (measured). The repo's record splits this as 3,891 removed at B=1 (≤ 1 px) and 2,545 at B=2 (in (1, 2] px); the split is the repo's, the total is verified. The "2,545" figure is an increment, not an error.
- Owner-reported scores: d2.8 0.2600 → champion 0.2778 (+0.0178). OWNER-REPORT.

**Why it scored highest (the repo's explanation, now checked against bytes):** removing dots next to known faults lowers false-positive mass where the hidden test is expected to have little truth. This raises DTI under α=0.2, β=0.8. The explanation requires the organizer's hidden test to down-weight catalogue faults. The repo asserts this in its pre-registration (`docs/research/h-apart3-1-cfkc-dhc-preregistration-20261027.md`). It could not be checked against DrivenData from this sandbox, so it remains **unverified**.

## 7. E1 gates (pre-registered order)

| Gate | Rule | Result |
|---|---|---|
| 1 Method canary | synthetic 1/R source recovered within 60 m (analytic) / 150 m (FFT) | PASS (`tests/test_euler_n1.py`, 4/4) |
| 2 Leakage canary | single-feature AUC vs catalogue ≤ 0.90 | PASS, AUC 0.530 |
| 3 Format | `check_submission.py --strict-finite` | PASS: float32, values {0,1}, zero outside footprint, EPSG:32611, 3730×3292, template transform |
| 4 Holdout vs incumbent | HIDE-RECOVER > champion 0.00452 | PASS, 0.01955 [0.01569, 0.02357], n=22,232 HOLDOUT-DTI — but the gate is non-discriminating (IR-4) |
| 5 SGMC non-regression | SGMC-CAL ≥ champion 0.0641 | **FAIL**, 0.01468 [0.01234, 0.01708], n=62,703 HOLDOUT-DTI; below random 0.0468 |
| 6 Uniqueness (literal) | Spearman ≤ 0.90 AND ≤ 70% of dots within 3 px, each registry raster | **FAIL**, 4 of 131 flagged. Worst: 13GEMSDOE lattice (206,895 dots), forward 99.97%, reverse 4.1% |

Gate 6 was run against 117 ledger rasters plus 9 focus files, not the full registry. Surfaces were binary rasters (the candidate's continuous density was not saved).

Verdict: **negative** (gate 5 fails; gate 6 fails). Gate 1–3 pass.

Analog projection (not a score): ledger rasters with SGMC-CAL in [0, 0.02) (n=13) have owner-reported scores with median 0.0187 (range 0.00–0.045). This is what E1's SGMC value resembles.

## 8. Irregularities flagged for review

- **IR-1 Leaderboard conflict.** Prompt: 0.4413 and 0.3195. Repo: 0.4437 (xiaofanhu, read 2026-10-26) and 0.4544 (2026-10-30). No live read possible today (HTTP 000). Use none as a current reference without a live check.
- **IR-2 GEMSDOE25 vs GEMSDOE30.** Not byte-identical: SHA-256 `91eae1ca…` (25) vs `8cf893ea…` (30). Same positive dot mask; GEMSDOE30 is zero-filled (0 NaN). The earlier phrase "byte-identical" was wrong and is corrected.
- **IR-3 Uniqueness metric is density-driven.** A dense registry raster makes almost any candidate look like a duplicate in the forward direction. The reverse direction (fraction of the registry's dots near the candidate) is 4.1% for the flagged lattice. The literal rule was not waived. Owner decision needed on a chance-corrected metric (for example, compare forward overlap with the overlap expected under random placement at the same density).
- **IR-4 HIDE-RECOVER holdout rewards catalogue-proximate dots.** Random dots score 10× the champion. The shared evaluator reproduces its recorded values exactly; the issue is the instrument design, not a coding error. Do not select a file on HIDE-RECOVER alone.
- **IR-5 NaN rule unverified.** The repo states the official page allows NaN outside the footprint; this could not be re-read here. The owner-mirrored template itself carries that pattern. The strict validator is stricter than the template.
- **IR-6 Owner NaN scores vs portal error.** NaN files show owner-reported scores, yet the user saw a range error on an uploaded file. Unresolved; needs the file name and portal text.
- **IR-7 Gate note cites DrivenData page 967** (`evidence/nine_site_verification_20261030.json`, `gate_note`). Not re-read this session.
- **IR-8 Lane not assigned.** The parallel-run method paragraph is not in the prompt. E1 was chosen from the repo's shortlist, not from an assigned lane.
- **IR-9 Full registry not rerun.** The 2026-10-28 scan (784 unique rasters) is cited, not re-verified.
- **IR-10 SGMC proxy non-monotonic.** Rank correlation with owner scores is +0.40 (n=117), but bins are not monotonic (≥0.10 bin median 0.07; 0.055–0.064 bin median 0.23). Use as a rank tool only.
- **IR-11 Nine-site association is n=9.** ρ = +0.95 (owner vs SGMC-CAL) and ρ = +1.00 (owner vs share beyond 1 km) come from one family of nine files and are not evidence of a general rule.
- **IR-12 Main-branch CTAs overstated.** Merged main showed "Download: YES" for H-GEO-1 and "OK TO DOWNLOAD ONLY" for H1, while `registry/current_status.json` says `any_file_ok_to_submit=false`. Re-checked from bytes with the same comparison as E1: H-GEO-1 7/131 flagged, worst 99.94% (13GEMSDOE); H1 7/131 flagged, worst 99.78% (13GEMSDOE). Both CTAs removed here. Evidence: `evidence/hgeo1_uniqueness_recheck_20261031.json`, `evidence/h1_uniqueness_recheck_20261031.json`.
- **IR-13 H-GEO-1 card verdict "promote" conflicts with its own fields.** Its SGMC-CAL is 0.0405 [0.0321, 0.0490] vs champion 0.0641 (a regression), and its lane check shows `lane_pass: false` (99.94%). Its README claim "UNIQUE vs all scored registry rasters (max 46.24%)" is not reproduced. Needs owner review of that card.
- **IR-14 Evaluator labels differ.** E1 and H-GEO-1 are labelled GEMSDOE32-HIDE-RECOVER-v3.0; H1 is labelled GEMSDOE32-HOLDOUT-v3-visible-gated (same n=22,232). Not reconciled. Each number is reported under its recorded label.

Legacy IDs: `IR-E1-01` (run card, Key Results) = IR-3; `IR-E1-02` = IR-4. The run card text is left unchanged; this section is the canonical numbering used by the executive summary and README.

## 8a. Merge with main (2026-10-31)

- Main had moved to `0acfc77` (PRs #46–#49, other sessions). Conflicts in `scripts/build_review_site.py` and the two executive-summary pages were resolved by keeping this branch's decision block first, then main's latest-review block. The generator output is the single source of the pages; `registry/current_status.json` was kept as main has it.
- The main-branch H-GEO-1 and H1 download CTAs were withdrawn (IR-12). Their files remain in `docs/downloads/` for audit; no file is cleared.
- Main's H-GEO-1 summary text is recoverable from git history at `origin/main` (commit c1990a7 and its merges).

## 9. Limits

- Cannot reach DrivenData, NLR, USGS, EPSG, or the owner Pages sites from this sandbox. The organizer template and the official metric code are not available; format checks use an owner-mirrored template.
- Cannot read the live leaderboard or the submission receipt.
- Full registry uniqueness not rerun; E1 uniqueness uses 131 rasters.
- One experiment only (budget 3). No hyperparameter tuning was done after the holdout result, to avoid overfitting the holdout.

## 10. Next steps (ranked by decision value)

1. Resolve the NaN rule with the organizer (or obtain the NLR spec text). This decides whether the zero-fill family is usable at all.
2. Owner decision on a density-corrected uniqueness metric (IR-3). Without it, no dense-family candidate can pass the literal rule.
3. Run candidate 2 (gravity–magnetic cross-gradient) under the same protocol, with SGMC non-regression tested before the uniqueness step.
4. Live leaderboard read from a reachable machine, to settle IR-1.

## Sources (official or verified, for manual review)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ (unreachable from sandbox, 2026-10-31)
- Problem page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (unreachable)
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ (unreachable)
- Submission format PDF (NLR): https://docs.nlr.gov/docs/fy26osti/96647.pdf (unreachable)
- Reference solution, reachable and read: https://github.com/drivendataorg/gems-prize-reference-solution (commit `aebe92f`)
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (unreachable)
- EPSG:32611: https://epsg.io/32611 (unreachable)
- Tversky index (metric family): https://en.wikipedia.org/wiki/Tversky_index
