# Candidate research directions — 2026-10-30 (ranked)

Untested research proposals, not assigned lanes or validated methods. Ranking is qualitative and speculative. No claim of novelty across other projects. None is authorized for a parallel run until it passes feature-level leakage canaries (AUC <= 0.90), a visible-only buffered segment holdout, the pre/post-placement registry gates, a comparison with a matching incumbent, and a separate slot-selection decision. Holdout metrics are proxies; no live score may be projected without validated calibration.

## H-SEISMIC — WITHDRAWN, NOT CLEARED (historical experiment)

**Do not download or submit this artifact.** The original run card's `ok_to_download: true` and `ok_to_submit: true` fields are superseded by the fail-closed release review. The candidate does not beat the same-evaluator holdout incumbent, and its uniqueness comparison covered only 15 local rasters rather than the complete registry. The file remains available in the repository as an audit artifact, not as a submission recommendation.

| Candidate / cost | Layers and proposed signature | Recorded evidence and superseding decision |
|---|---|---|
| **H-SEISMIC / low (withdrawn)** | USGS ANSS ComCat hypocenters (external/usgs_comcat_geodawn.csv, magnitude >=3, valid GeoDAWN footprint), magnitude-weighted and smoothed with the 300 m triangular kernel; masked to the USGS SGMC off-catalogue trace band at 100 m–1.2 km, excluding catalogue faults plus 200 m collar; Poisson-disk d=2.6 px; 30,000 dots. | Artifact: `docs/downloads/gemsdoe32-hseismic-comcat-sgmc-b2-20261030T020420Z-a1200c82-zeros.tif` (SHA-256 `3cf5774b2fe9bcab97988480e4da011ddf4fe9f90214e1696d24ca7c4d3b4c23`). Local format/range checks pass. `HOLDOUT-DTI` (GEMSDOE32-HOLDOUT-v3-visible-gated; 22,232 withheld positives): 0.003857 [0.003132, 0.004612], below the incumbent 0.004515 [0.003816, 0.005262]; it fails the repo's required same-evaluator holdout-improvement gate. SGMC off-catalogue calibrated `HOLDOUT-DTI` is 0.1049 [0.0923, 0.1170] versus incumbent 0.06412 [0.05673, 0.07165], but this proxy is not a competition-score projection or selector approval. Leakage canaries max AUC 0.5034. Uniqueness was checked against 15 local comparators only; full-registry uniqueness was not established. No weekly slot was claimed. **Verdict: negative; do not download or submit.** See `README.md`, `evidence/GEMSDOE32-H-SEISMIC-20261030T020420Z-run-card.json`, and `registry/irregularities.json`.

## Carried forward from 2026-10-28 (untested)

| Rank / cost | Layers and proposed signature | Geological rationale & non-fault mimic |
|---|---|---|
| **2 / low-medium** (H-SEISMIC is the ComCat half of this) | USGS ANSS ComCat post-2021 hypocenters + B06 `tc` + lidar-scarf features; clustering of modern earthquakes over radiometric anomalies and subtle scarps. | Post-2021 seismicity records slip on faults too young or blind for the catalogue. Mimics: aftershocks on known faults, mining blasts, array artifacts. Requires ComCat provenance check (`external/usgs_comcat_provenance.json`). |
| **3 / medium** | USGS 3DEP 10 m fluvial chi gradient & knickzones + B13 `iso_grav_anom` / B04 `geod_2ndinv`. | Fault-controlled baselevel change; blind faults can drain catchments without mapped traces. Mimics: lithologic resistance, landslide dams, volcanic deposits. |
| **4 / low** | B16 `depth_to_base_surf` + B07 `geod_shearrate` + B08 `geod_dilaterate` + B17 `cond_surf`. | Shallow actively shearing conductive basement = blind geothermal upflow setting. Mimics: basin edges, conductive clay layers without flow. |
| **5 / low-medium** | US BLM MLRS closed geothermal/lode claims distance + USGS Qfault traces; annulus just outside mapped traces near closed claims. | Closed claims mark past geothermal interest; blind extensions beyond mapped traces plausible. Mimics: non-geothermal claim clustering, cultural noise. |

## Notes on the incumbent and leaderboard context

- GEMSDOE32 champion (owner-report 0.2778, SHA c55bafc4...) is a dotted, catalogue-proximate submission; the nine focus-site best artifacts are pairwise near-duplicates of one H19-5 ridge-dotted raster (audit: up to 100% within-3-px overlap, |rho| up to 1.0000).
- Leaderboard high 0.4437 (team xiaofanhu, read 2026-10-26T04:32:28Z, public page only).
- H-SEISMIC deliberately hunts faults MISSING from the catalogue (blind/creeping seismicity + pre-Quaternary SGMC structures) rather than duplicating catalogue-proximate dots.
