# Candidate research directions — 2026-10-30 (ranked)

Untested research proposals, not assigned lanes or validated methods. Ranking is qualitative and speculative. No claim of novelty across other projects. None is authorized for a parallel run until it passes feature-level leakage canaries (AUC <= 0.90), a visible-only buffered segment holdout, the pre/post-placement registry gates, a comparison with a matching incumbent, and a separate slot-selection decision. Holdout metrics are proxies; no live score may be projected without validated calibration.

## Implemented this session — H-SEISMIC (submission candidate)

| Rank / cost | Layers and proposed signature | Result (this session, holdout HOLDOUT-DTI) |
|---|---|---|
| **1 / low** (IMPLEMENTED — format-valid, unique, ok_to_download) | USGS ANSS ComCat hypocenters (external/usgs_comcat_geodawn.csv, mag>=3, valid GeoDAWN footprint) magnitude-weighted and smoothed with the official 300 m triangular kernel, masked to USGS SGMC off-catalogue trace band at 100 m–1.2 km (100 m raster), excluding catalogue faults + 200 m collar; Poisson-disk d=2.6 px; 30,000 dots. | Artefact: docs/downloads/gemsdoe32-hseismic-comcat-sgmc-b2-20261030T020420Z-a1200c82-zeros.tif (SHA-256 3cf5774b...c4d3b4c23, 179,852 bytes). 13/13 format/range checks pass (EPSG:32611, 3730x3292, template transform, [0,1], no NaN anywhere, zero on-catalogue pixels). Holdout: pooled DTI 0.00386 [0.00313, 0.00461] vs GEMSDOE32 champion flat-mask proxy 0.00452 (CI overlaps); SGMC off-catalogue calibrated DTI 0.1049 [0.0923, 0.1170] vs champion 0.06412 (+63.6%); drift-corrected 0.05569 vs 0.04504. Leakage canaries max AUC 0.5034 <= 0.90 PASS. Uniqueness vs all locally available comparators: max |rho| 0.7613 <= 0.90, max within-3-px overlap 29.97% <= 70% (vs champion rho -0.7051, overlap 21.67%/19.72%); registry rasters were not present on disk in this checkout so the scan covers champion + lane artifacts + the apart3 negative artifact. ok_to_submit=true per local gates; weekly slot NOT claimed; submission to DrivenData competition 306 is manual (name GEMSDOE32-H-SEISMIC-20261030T020420Z, note 120 chars). Not organizer-confirmed. |

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
