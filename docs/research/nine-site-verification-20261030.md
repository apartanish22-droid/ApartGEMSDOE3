# Nine-site verification, "why 0.2778", and the submission decision — 2026-10-30

**Decision: no file from this repository is authorized for download or upload.** No new GeoTIFF was generated in this session. The reasons are below. Every number here is labelled with its evidence class:

- **OWNER-REPORT** — score copied from the supplied prompt or the repo audit; no organizer receipt.
- **HOLDOUT-DTI** — computed by the shared evaluator `scripts/evaluate_holdout.py` (`GEMSDOE32-HIDE-RECOVER-v3.0` and `GEMSDOE32-SGMC-CAL-v3.0`), with withheld-positive count and 95% cluster-bootstrap CI.
- **PUBLIC-LEADERBOARD-OBSERVATION** — read from the public leaderboard page on 2026-10-30; the fetch tool returns no snapshot timestamp.
- **GEOMETRY** — computed from raster bytes; not a score.

Reproduce: `.venv/bin/python scripts/verify_nine_site.py` → `evidence/nine_site_verification_20261030.json` (about 95 s). Regression test: `tests/test_nine_site_verification.py`.

---

## 1. Official rules this analysis relies on (verified)

Source: [DrivenData problem description, page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (fetched 2026-10-30).

| Rule | Verbatim or close paraphrase from the page | Consequence here |
|---|---|---|
| Test target | "faults that are not contained within the current public USGS database" comprise the test dataset. | Inference: dots within a few hundred metres of catalogue faults are mostly false-positive mass for the official test. |
| Metric | Distance-weighted Tversky index, α = 0.2 (FP), β = 0.8 (FN), triangular kernel R = 300 m. | Dots are cheap to add (α = 0.2) but missing truth is expensive (β = 0.8). |
| Format | float32, single band, UTM 11N EPSG:32611, 100 m, same bounds; "data outside the bounds is null or nan"; values between 0 and 1. | NaN outside the footprint is **allowed by the spec**. See §4. |
| Rounds | Initial round scored on a private set; final round rescored on an expanded label set; "Competitors must choose a **single** submission for scoring across both rounds." | Choosing a file is a strategic decision, not a retry loop. |

Official metric note: the page writes `DTI = TP_w / (TP_w + α·FP_w + β·FN_w + ε)`; `repo src/gems32/metric.py` and `docs/research/why-02778-reported-score.md` use the same form.

## 2. Public leaderboard (PUBLIC-LEADERBOARD-OBSERVATION)

Source: [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), fetched 2026-10-30. Full rows: `evidence/leaderboard_snapshot_20261030_fetch.json`.

- #1 xiaofanhu **0.4544**; #2 cfld__ 0.3916; #3 Batik Shirt Brothers 0.3911; #4 BrandenKMurray 0.3841; #5 op01 0.3642.
- The nine focus sites sit at 0.24–0.28 (OWNER-REPORT). The gap to #1 is about 0.18 on the public split.

**Irregularity — please review:** the prompts say 0.4413 (top) and 0.3195 ("highest right now"). `registry/current_status.json` records 0.4437 read 2026-10-26. This fetch shows 0.4544. None of these is a score for this repository's files, and snapshot times differ.

## 3. Nine-site table (bytes verified; scores labelled)

All nine files were re-hashed from their bytes. Five were fetched from pinned GitHub refs in `registry/focus_registry_manifest.json` and matched their pinned SHA-256 values. Holdout: 22,232 withheld positives, 140 spatial clusters, 1000 bootstrap reps. The CI column is the evaluator's 95% cluster-bootstrap interval.

| Site | Reported score (OWNER-REPORT) | Holdout DTI, catalogue-withheld (HOLDOUT-DTI) [95% CI] | SGMC off-catalogue calibrated DTI (HOLDOUT-DTI) [95% CI] | Dots >1 km from any catalogue fault | Strict repo validator (finite + [0,1]) | File to download? | Unique? |
|---|---:|---|---|---:|---|---|---|
| GEMSDOE24 | 0.2477 | 0.0932 [0.0813, 0.1060] | 0.0579 [0.0511, 0.0652] | 59.3% | FAIL — 7,111,787 NaN outside footprint | **No** | No (see §5) |
| GEMSDOE25 | 0.2600 | 0.0967 [0.0842, 0.1095] | 0.0606 [0.0536, 0.0679] | 59.6% | FAIL — NaN outside footprint | **No** | No |
| GEMSDOE27 | 0.2449 | 0.0927 [0.0809, 0.1054] | 0.0583 [0.0515, 0.0655] | 58.4% | FAIL — NaN outside footprint | **No** | No |
| GEMSDOE28 | 0.2710 | 0.0294 [0.0250, 0.0344] | 0.0630 [0.0557, 0.0704] | 65.7% | FAIL — NaN outside footprint | **No** | No |
| GEMSDOE30 | 0.2600 | 0.0967 [0.0842, 0.1095] | 0.0606 [0.0536, 0.0679] | 59.6% | PASS | **No** — identical prediction to GEMSDOE25 | No |
| GEMSDOE31 | 0.2708 | 0.0305 [0.0257, 0.0361] | 0.0630 [0.0558, 0.0704] | 65.4% | FAIL — NaN outside footprint | **No** | No |
| GEMSDOE32 | **0.2778** (highest) | 0.0045 [0.0038, 0.0053] | 0.0641 [0.0567, 0.0716] | 69.8% | PASS | **No** — already submitted per the registry record; resubmitting adds nothing | No (100% of dots within 3 px of GEMSDOE24, 25, 27, 30, 31, 33, 36; 99.9% of GEMSDOE28) |
| GEMSDOE33 | 0.2632 | 0.0520 [0.0458, 0.0583] | 0.0626 [0.0553, 0.0700] | 63.4% | PASS | **No** | No |
| GEMSDOE36 | 0.2750 | 0.0046 [0.0039, 0.0053] | 0.0644 [0.0571, 0.0720] | 69.7% | PASS | **No** | No (97.3–97.6% of dots within 3 px of each of GEMSDOE24, 25, 27, 28, 30, 31, 32, 33) |

**Estimated score for a new submission:** not estimable. A HOLDOUT-DTI value cannot be converted to a live score without a validated calibration study, and no new candidate exists.

**Format note.** The official spec permits NaN outside the bounds. The repo's strict validator is more conservative: it requires whole-array finiteness. Those two rules disagree, so "PASS" under the strict validator is a safety check, not an official requirement. I did **not** confirm the cause of the portal's "Predicted values must be in range [0, 1]" message. The NaN files are the only ones that fail the strict check; the cause is unverified.

**Do not** re-save a NaN file with zeros to get past the error. That creates a reformatted copy of an existing submission, which the protocol excludes.

## 4. Why the NaN files fail the repo's check (GEOMETRY)

- GEMSDOE24, 25, 27, 28, 31: each has 7,111,787 NaN pixels, equal to the count outside the 5,167,373-pixel footprint. Their values inside the footprint are in [0, 1].
- GEMSDOE30, 32, 33, 36: zero NaN pixels; every pixel finite and in [0, 1].
- GEMSDOE30 is the same prediction as GEMSDOE25 with NaN replaced by zero (identical positive masks and identical values after NaN→0), but both report 0.2600.

## 5. Uniqueness (GEOMETRY)

Protocol gate: a candidate fails if more than 70% of its dots lie within 3 px of any one registry raster, or if its absolute Spearman correlation with any registry raster exceeds 0.90.

- Across the nine files: **all 36 pairs** exceed 70% in at least one direction. The weakest pair is GEMSDOE28 vs GEMSDOE36 at 97.3%.
- The full registry has 451 rasters (`registry/focus_registry_manifest.json`, about 375 MB). The full-registry check has **not been run**, so no new file can be called unique.

## 6. Why did GEMSDOE32 (0.2778) score highest? — hypotheses with evidence grades

**Mechanism (strong on the official metric, not proven for the leaderboard).** The test truth is new faults outside the USGS catalogue. A dot placed within a few hundred metres of a catalogue fault is therefore mostly a false positive for the test. Under α = 0.2, that dot adds a small amount to the denominator and gains almost no TP. Removing catalogue-adjacent dots lowers the denominator without losing TP, which raises DTI. The owner-reported nested ladder is consistent with this: H19-5 (121,131 dots, 0.1922) → d2.8 (44,090, 0.2600) → solo B=1 (40,199, 0.2708) → champion B=2 (37,654, 0.2778). Here B=2 excludes dots within two pixels of the training catalogue (`docs/research/why-02778-reported-score.md`).

**Evidence in this repo's nine files (n = 9; OWNER-REPORT scores; association only):**

- Owner score vs share of dots more than 1 km from any catalogue fault: Spearman ρ = **+1.00** (n = 9).
- Owner score vs SGMC off-catalogue calibrated DTI (HOLDOUT-DTI): ρ = **+0.95**, p ≈ 9×10⁻⁵.
- Owner score vs catalogue-withheld holdout DTI: ρ = **−0.85**, p = 0.004. **The repo's primary holdout ranks these files in reverse.** The files it scores highest (GEMSDOE24, 25, 27, 30) are the ones with the most catalogue-adjacent dots, and the scores it scores lowest are the leaderboard leaders.

**Interpretation.** The catalogue-withheld hide-and-recover gate rewards recovering withheld *catalogue* faults. The official test set, as the page describes it, consists of faults not in the USGS database, so this gate optimises a different target from the one scored. The four lowest owner-reported files (GEMSDOE27, 24, 25, 30; 0.2449–0.2600) have the highest holdout DTI (about 0.09). The two highest-scoring files, GEMSDOE32 and 36, have the lowest (about 0.0045). The SGMC off-catalogue proxy is closer to the official target and tracks the owner scores in this small sample.

**Alternative explanations (not excluded):**

1. Sampling noise on the public split. The leaderboard shows public-only scores, and the prize depends on private and expanded labels.
2. The top four files (0.2708–0.2778) differ by under 0.01, and no receipt or CI exists for the owner values. Ranking within the top four is not established.
3. Shared lineage: all nine are variants of one family, so their similarity is expected and does not isolate the cause.

**Can we beat 0.2778?** Possibly, but not by pruning this family further. The family is already about 70% beyond 1 km from the catalogue, and pushing the cutoff further risks removing genuine new faults near old ones. Closing the gap to the public #1 (0.4544) requires new true positives, which the current holdout cannot measure. **No unique candidate has been validated, so no claim about exceeding 0.2778 is made.**

## 7. Candidate hypotheses (ranked; none run)

Ranking is a judgement ordering by expected information value and implementation cost. **Expected DTI improvement for every candidate is not estimable** until a candidate is validated.

Novelty was checked by identifier search in `src/gems32` and `src/gemsdoe32` (`grep -i`). An identifier match is a lead for code review, not proof of overlap.

| Rank | Hypothesis (layers) | Physical signature | Why it targets off-catalogue faults | Named non-fault mimic | Overlap with existing code | Cost |
|---|---|---|---|---|---|---|
| **1** | **H-A — Selection signal change (methodology, not a fault map).** Replace the catalogue-withheld holdout with an off-catalogue objective (SGMC calibrated proxy, or a catalogue-buffered variant) as the selection gate. | Not a geophysical signature. Measures off-catalogue recovery. | Matches the official test design (new faults only). | Overfitting the SGMC geology map (a Quaternary-fault proxy with its own bias). | Gate change, not a feature. Requires user approval because it changes the protocol. | Low |
| 2 | **H-B — Directional semivariogram anisotropy of potential-field residuals.** Layers: band 2 `rtp`, band 13 `iso_grav_anom` (verified against `data/prepared_manifest.json`). Use only pixels > 1 km from catalogue. | Short-range along-strike continuity exceeding cross-strike continuity. | A fractured or offset basement corridor can produce strike-aligned texture under cover. | Flight-line direction artefacts in GeoDAWN. Control with `external/acquisition_block_id_100m.tif`. | No identifier match for "semivariogram". The word "anisotrop" appears in 9 modules; code review needed. | Medium |
| 3 | **H-C — Signed magnetic–gravity edge offset.** Layers: band 2 `rtp`, band 13 `iso_grav_anom`, band 18 `iso_grav_anom_hg`. | Repeatable signed displacement between magnetic and gravity edges along the edge normal. | A faulted basement contact can separate shallow magnetic edges from deeper gravity edges. | Differing transfer functions or source depths (e.g., deeper plutons). | No identifier match for "cross-edge". | High |
| 4 | **H-D — Signed cross-front topographic asymmetry.** Layers: band 12 `det_elev`, band 19 `det_elev_slope`. | Signed elevation asymmetry across off-catalogue edges. | Tilted or blind range fronts can leave a coherent asymmetric profile after scarps degrade. | Aspect-controlled erosion (north- vs south-facing slopes). | **Partial overlap.** `src/gems32/juxtaposition.py` already implements step-vs-ramp profiles (A48-H1 JXSTEP, including `det_elev` roughness) and R6-1 for elevation. Only the signed-asymmetry element may be new. | Low–medium |

**Demoted from the prior shortlist:** the "buried basement-step ridge with quiescence gate" listed first in `docs/research/next-hypotheses-review-20261028.md` overlaps `src/gems32/juxtaposition.py` (A48-H1 JXSTEP, bands 15, 13, 12, 6, 17). It is not a new hypothesis.

## 8. Limits of this session

- The assigned method paragraph is absent from the prompt and from the checkout (`README.md` says do not infer it). Without a lane, no method experiment can be registered or counted.
- The organizer training data is not accessible. The sandbox cannot reach DrivenData, Dropbox, GDR OpenEI, or USGS (connection failed). The 36 restored files come from a third-party GitHub mirror pinned by SHA-256 (`registry/data_manifest.json`). They are **not organizer-authenticated**.
- The full 451-raster registry is not restored, so the uniqueness gate cannot be completed.
- No holdout-validated candidate exists, so there is nothing to submit.

## 9. Run card (diagnostic session; no candidate)

```json
{
  "hypothesis": "No new method hypothesis tested. Diagnostic: the catalogue-withheld holdout and the official off-catalogue test target are misaligned, and on nine owner-reported files the holdout ranks the leaderboard in reverse.",
  "mechanism": "Official test truth excludes USGS-catalogue faults; dots near catalogue faults are mostly FP mass under alpha=0.2.",
  "named_non_fault_mimic": "Shared lineage of the nine variants; public-split sampling noise on OWNER-REPORT scores.",
  "holdout_dti": "Nine files, HOLDOUT-DTI with evaluator GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 withheld positives, 95% cluster-bootstrap CI per file (see section 3). Best owner-reported file GEMSDOE32: 0.0045 [0.0038, 0.0053].",
  "correlation_overlap_vs_registry": "Nine-site pairwise only: all 36 pairs > 70% within 3 px in at least one direction. Full 451-raster registry NOT RUN.",
  "raster_sha256": {"GEMSDOE32_zeros": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"},
  "validator_output": "Strict repo validator: PASS for GEMSDOE30, 32, 33, 36; FAIL for 24, 25, 27, 28, 31 (NaN outside footprint). Official spec permits NaN outside bounds; portal message cause unverified.",
  "submission_name": null,
  "submission_note": "No submission. Diagnostic only.",
  "verdict": "negative"
}
```

## 10. Sources (manual review)

- [DrivenData problem description (page 967)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — metric, test set, format.
- [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — public observation on 2026-10-30.
- [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login required; not accessible from this sandbox.
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/).
- [EPSG:32611 (UTM 11N)](https://epsg.io/32611).
- [Tversky index](https://en.wikipedia.org/wiki/Tversky_index).
- Repo records: `evidence/nine_site_best_files_audit.json`, `evidence/nine_site_verification_20261030.json`, `registry/focus_registry_manifest.json`, `registry/data_manifest.json`, `docs/research/why-02778-reported-score.md`.
