# H-S1 and H-M1 — holdout and uniqueness results, 2026-10-31

**Decision: both negative. DO NOT SUBMIT.** Neither candidate clears the off-catalogue (SGMC) gate against the GEMSDOE32 incumbent. Neither has an assigned lane or a selector authorization. The live score is NOT ESTIMABLE.

Labels: **HOLDOUT-DTI** = evaluator version, withheld-positive count, 95% cluster-bootstrap CI (140 spatial clusters, 1000 reps). **OWNER-REPORT** = owner-reported leaderboard value, not reproducible from the holdout. No ORGANIZER-CONFIRMED values exist for these files.

Machine-readable summary: `evidence/candidates_20261031_summary.json`. Repo review and irregularity list: `docs/repo-review-2026-10-31.md`. Ranked hypotheses: `docs/research/h-candidates-20261031.md`.

## Holdout comparison

| Quantity | GEMSDOE32 incumbent | H-S1 (exp 1) | H-M1 (exp 2) |
|---|---|---|---|
| Catalogue-withheld HOLDOUT-DTI (hide-and-recover) | 0.0045 [0.0038, 0.0053] | 0.0213 [0.0163, 0.0258] | 0.0304 [0.0243, 0.0366] |
| SGMC off-catalogue, prevalence-calibrated HOLDOUT-DTI | **0.0641 [0.0567, 0.0716]** | 0.0246 [0.0181, 0.0322] | 0.0340 [0.0275, 0.0411] |
| SGMC raw pooled DTI | 0.0961 [0.0857, 0.1071] | 0.0380 | 0.0508 [0.0401, 0.0639] |
| Withheld positives (catalogue / SGMC) | 22,232 / 62,703 | 22,232 / 62,703 | 22,232 / 62,703 |
| Evaluator | GEMSDOE32-HIDE-RECOVER-v3.0 / GEMSDOE32-SGMC-CAL-v3.0 | same | same |
| Dots after label mask | 37,654 | 40,732 | 36,681 |
| Owner-reported live score | 0.2778 (OWNER-REPORT) | none | none |

Gate result: the SGMC gate requires the candidate to match or beat the incumbent. H-S1 is 0.0246 vs 0.0641 (2.6× short). H-M1 is 0.0340 vs 0.0641 (1.9× short). Both fail.

The H-M1 catalogue-withheld value is above the incumbent's, and the two CIs do not overlap. That does not pass the gate, because the gate is the off-catalogue proxy. It is a sign that the catalogue-holdout signal and the off-catalogue signal disagree, which matches the repo's earlier finding (IR-20261031-05). A paired same-evaluator CI was not computed for either candidate.

## Experiment 1 — H-S1 spectral roll-off

- **Hypothesis:** oriented 2-km line integrals of the local flatness anomaly of the 3.2-km-window magnetic (rtp) power-spectrum slope mark linear damage-zone texture not visible as edges.
- **Mechanism:** fracture damage zones add high-wavenumber power, flattening the local spectral slope. An 8-orientation max-of-line-means keeps only linear responses.
- **Named non-fault mimic:** magnetite-heterogeneous lithology and flight-line artefacts (tested with acquisition-block eta² and rtp-amplitude Spearman).
- **Controls:** acquisition-block eta² 3.1e-7; Spearman(surface, rtp amplitude) −0.037. No flight-line or amplitude artefact detected.
- **Leakage canary (single-feature holdout AUC, seed 20):** rtp band 2 raw 0.510; spectral flatness z 0.525; H-S1 surface 0.526. All below 0.90.
- **Surface:** 754,800 windows, 310,607 valid (≥ 90% coverage); min −6.64, max 3.20; finite within the footprint.
- **Candidate file:** `docs/downloads/gemsdoe32-h-specroll-h1-20261031T044136Z-ad93017d-zeros.tif`, SHA-256 `299647f911c31fd4b1942865330f932b9e6fec3d4fca824deebac1f3358275f6`. Submission name `H-SPECROLL-H1`.
- **Independent format check:** PASS (strict whole-array finite, [0, 1]).
- **Uniqueness:**
  - Surface stage: PASS. Worst |Spearman| 0.0464 (GEMSDOE91).
  - Final dots: FAIL under the literal rule. Seven rasters have 3-px overlap of 0.715 or higher and 3-px footprint coverage of 0.70 or higher:
    - GEMSDOE24 13gems lattice: overlap 1.00, coverage 0.999.
    - GEMSDOE3 pindrop-v4-nodes: overlap 0.715, coverage 0.735.
    - Four ApartGEMSDOE2 masks: overlap 1.00, coverage 1.00.
    - GEMSDOEkarage1 continuous raster: overlap 1.00, coverage 1.00.
  - All seven are dense or space-filling rasters. The highest overlap on any raster with 3-px coverage below 0.70 is 0.533, and none of those is a duplicate.
  - The scan records `audit_complete: false`: 6 registry rasters were malformed or missing and 2 were constant or empty. The result is therefore not a complete audit.
- **Submission note:** says "37654 dots". The raster has 40,732 (IR-20261031-02).
- **Verdict:** negative.

## Experiment 2 — H-M1 magnetic–gravity cross-gradient

- **Hypothesis:** co-located, co-oriented magnetic (rtp) and gravity (iso_grav_anom) edges mark offsets that cut both fields.
- **Mechanism:** a fault that juxtaposes contrasting magnetic and density blocks produces aligned gradients in both fields. The H35-C functional form scores that coincidence.
- **Named non-fault mimic:** intrusive or lithologic contacts with both a magnetic and a density contrast (the cross-gradient mimic).
- **Prior art (must be disclosed):** the H35-C form (cross-gradient product) already exists in `src/gems32/h35_new.py` for a different layer pair (conductivity × depth-to-base). The cross-gradient idea follows Gallardo & Meju (2004). H-M1 applies the form to a new layer pair. It is not new in method.
- **Controls:** acquisition-block eta² 0.0094 (about 1% of surface variance; small but nonzero).
- **Leakage canary (single-feature holdout AUC, seed 20):** rtp band 2 residual 0.513; iso_grav band 13 residual 0.535; H-M1 surface 0.519. All below 0.90.
- **Candidate file:** `docs/downloads/gemsdoe32-h-crossgrad-mg-h2-20261031T045331Z-8b399900-zeros.tif`, SHA-256 `15ca1f62b45dbe6715578982a84f812af151b91d857a65f8949ab5d7e57e6a3a`. Submission name `H-CROSSGRAD-MG-H2`.
- **Independent format check:** PASS (strict whole-array finite, [0, 1]).
- **Uniqueness** (`evidence/H-M1-CROSSGRAD-MG_registry_scan.json`, 1,092 registry rasters, 769 unique masks or surfaces):
  - Surface stage: PASS. Worst |Spearman| 0.132 (ApartGEMSDOE2 ridge raster).
  - Final dots: FAIL under the literal rule. Eight rasters have 3-px overlap of 0.717 or higher:
    - Seven dense rasters (3-px coverage 0.735 or higher): GEMSDOE24 13gems lattice (overlap 0.981), GEMSDOE3 pindrop-v4-nodes (0.717, coverage 0.735), four ApartGEMSDOE2 masks (1.00), GEMSDOEkarage1 continuous raster (1.00).
    - **One sparse raster:** GEMSDOE67 `gemsdoe67-ovtr-ml-cover-tau3p0-20261012-nan.tif`, overlap 0.746 at 3-px coverage 0.548. This is a non-dense duplicate, so H-M1's failure is not only the dense-raster artefact (IR-20261031-03 applies to H-S1 only).
  - The scan records `audit_complete: false` (6 malformed or missing rasters, 2 constant or empty).
- **Submission note:** says "37654 dots". The raster has 36,681 (IR-20261031-02).
- **Verdict:** negative.

## Why the proxy ranks these below the incumbent

Untested hypothesis: the incumbent's SGMC off-catalogue score (0.0641) may come from dots that sit on mapped off-catalogue fault traces, while both new candidates place dots on broader gradient and texture anomalies that the SGMC layer rewards less. The measured facts are narrower. Both candidates score higher on the catalogue-withheld holdout (0.0213 and 0.0304 vs 0.0045) and lower on the SGMC proxy (0.0246 and 0.0340 vs 0.0641). That matches the repo's earlier calibration finding that catalogue-holdout gains do not transfer to the off-catalogue proxy. Testing the hypothesis needs a per-dot attribution against the SGMC traces, which was not run.

## Limitations

- The SGMC proxy is a mapped-geology layer (Horton, San Juan & Stoeser 2017, USGS DS-1052, doi:10.5066/F7WH2N65, [source](https://ngmdb.usgs.gov/Prodesc/proddesc_105832.htm)). It is not the organizer's test set. Its agreement with the leaderboard is unknown.
- The holdout is hide-and-recover with spatial buffers. Its agreement with the leaderboard on owner data is weak (IR-20261031-05).
- The inputs are owner mirrors, not organizer-authenticated.
- The literal 3-px rule cannot separate full-footprint rasters (IR-20261031-03). The uniqueness failures above are reported under the rule as written.
- The lane is not assigned, so no run can be cleared for a weekly slot.
- Expected live DTI for any candidate is not estimable from these data.

## Next steps (for the next session, not authorized here)

1. Owner decision on the literal 3-px rule (IR-20261031-03).
2. Owner-assigned method lane (IR-20261031-04).
3. Compute a paired same-evaluator CI against the incumbent before any further holdout claim.
4. Regenerate submission notes with the actual dot counts (IR-20261031-02) if any candidate is promoted.
5. Third experiment reserved: H-B directional semivariogram (rank 3 in `docs/research/h-candidates-20261031.md`). Not started.
