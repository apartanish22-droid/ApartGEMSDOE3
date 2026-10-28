> **Historical research record; not a current release decision. DO NOT SUBMIT.** Prior promotion and score claims below have not been independently verified. See the [current review](https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/knowledge/09_release_recheck_and_hypotheses_20261028.md).

# Pre-Registration: ApartGEMSDOE3 (`H-APART-1: BHGC-3` through `H-APART-4: INSAR-3`)

- **Date:** 2026-10-27 (UTC)
- **Repository:** `apartanish22-droid/ApartGEMSDOE3`
- **Branch:** `arena/9293a496-apartgemsdoe3`
- **Evaluator Version:** `GEMSDOE32-HIDE-RECOVER-v3.0` ($n = 22,232$ withheld fault pixels across 30 spatially-blocked cells; $n = 15,504$ detached blind segments $\ge 600\text{ m}$) + untouched off-catalogue `GEMSDOE32-SGMC-CAL-v3.0` ($n = 62,703$ USGS SGMC fault pixels $> 300\text{ m}$ from `labels.tif`)
- **Experiment Budget (Protocol Rule 6):** At most **3 experiments** (`EXP-1`, `EXP-2`, `EXP-3`).

---

## 1. Four Ranked Candidate Geological Hypotheses (Pre-Implementation Ranking)

### Rank 1 (Selected Primary Hypothesis — `H-APART-1: BHGC-3`)
**Bi-Population Horst-Graben Gravity-Vector Divergence (`Band 18, Band 11`), Depth-Invariant Magnetic Tilt Wall, Piedmont-Toe Bedrock Contact Spine & PU-Safe 89-Channel Dual-Cover Hydrothermal-Vent OOF with Axial-Crest Submodular Emission**

- **Exact Layers Used:**
  - `training_features.tif` native horizontal gravity gradient vector `Band 18 (iso_grav_anom_hg = dg/dx)` and `Band 11 (iso_grav_anom_vg = dg/dy)`, `Band 5 (iso_grav_anom_slope)`, and `Band 15 (depth_to_base_surf)`.
  - `training_features.tif` magnetic bands `Band 6 (tc)`, `Band 3 (tmi_hg)`, `Band 9 (tmi_vg)`, `Band 2 (rtp)`, `Band 14 (tmi)`, and `Band 17 (cond_surf)`.
  - `training_features.tif` topographic/tectonic bands `Band 12 (det_elev)`, `Band 19 (det_elev_slope)`, `Band 4 (geod_2ndinv)`, `Band 7 (geod_shearrate)`, `Band 8 (geod_dilaterate)`, `Band 10 (deq_n100a15)`, `Band 16 (ieq_n100a15)`.
  - External verified public layers (`data/restore_receipt.json`): USGS 3DEP 1 m LiDAR (`1,053` tiles, `75.37%` footprint coverage), USGS GeoDAWN 4-block airborne radiometrics (`10.5066/P93LGLVQ`) + contractor block polygons, GDR #1391 (`10.15121/1881483`) 2-m temperature probe surveys, thermal wells/springs, and travertine/tufa/opaline sinter vents, BLM LRS geothermal mining claims, and US Census TIGER/Line roads (`tl_2023_32_prisecroads` + `tl_2023_32001_roads`).
- **Physical Signature / Mathematical Transform:**
  1. **Laplace-Harmonic Gravity-Vector Divergence (`grav_vec_div_crest`):** By Laplace's equation $\nabla^2 g = 0$ in the source-free upper half-space (Blakely 1995, Ch. 12), the horizontal divergence of the pre-computed gravity gradient vector $\mathbf{g}_H = (\text{Band }18, \text{Band }11)$ equals the negative second vertical derivative:
     $$\nabla_H \cdot \mathbf{g}_H = \frac{\partial(\text{Band }18)}{\partial x} + \frac{\partial(\text{Band }11)}{\partial y} = -\frac{\partial^2 g}{\partial z^2}$$
     Combined with the Blakely-Simpson (1986) cross-contact inflection crest $-\partial^2 \|\mathbf{g}_H\| / \partial n_g^2$ along $\hat{\mathbf{n}}_g = \mathbf{g}_H / \|\mathbf{g}_H\|$ and basement throw $\|\nabla(\text{Band }15)\|_2$, this localizes blind intrabasin normal fault contacts directly beneath $50\text{–}600\text{ m}$ of unconsolidated basin fill without cascading finite-difference noise on `Band 1`.
  2. **Miller-Singh Magnetic Tilt-Angle Zero-Crossing Wall (`mag_tilt_zerocross_wall`):** Extracts the zero-crossing wall of `Band 6 (tc)` (Miller & Singh 1994; Verduzco et al. 2004) weighted by `Band 3 (tmi_hg)` and `Band 9 (tmi_vg)` to trace depth-invariant sub-vertical basement fault contacts.
  3. **Multi-Scale Piedmont-Horst Bedrock Contact Spine (`piedmont_horst_step_spine`):** Multi-scale Hessian ridge maxima (`ridge_s1, ridge_s2, ridge_s3`), `tophat2`, and `Band 19` piedmont-toe slope break, explicitly de-confounded against Pleistocene Lake Lahontan (~1,330 m Sehoo / ~1,235 m Fallon) wave-cut shorelines and TIGER road/rail prisms, and suppressed inside deep flat playa interiors (`depth > 320 m`, `slope < 1.6 deg`).
  4. **PU-Safe Collar-Hardened 89-Ch / 76-Ch Dual-Cover OOF + Distance-Balanced Far-Field Spine:** Fixes `H48-1-FBGR`'s `2.0 < d_tr < 5.0 px` negative-sampling blind spot by sampling non-crest negatives in `2.4 <= d_tr < 5.5 px` while applying Positive-Unlabeled (PU) reliable-negative filtering (Elkan & Noto 2008) in the far field (`d_tr > 8 px`), and balances near-field OOF relay continuation with a stationary far-field structural-geothermal spine floor.
- **Why It Catches Unmapped Faults Missing from USGS/INGENIOUS:**
  - Live-score forensics across 111 scored rasters (`evidence/livescore_forensics_20261027.json`) prove that the hidden benchmark contains **two distinct populations**: (i) near-field unmapped splays/relays (`0.2–1.5 km`), and (ii) `52.4%–58.4%` far-field (`> 1.5 km`) unmapped range-bounding piedmont/horst faults and concealed intrabasin basement steps (where `GEMSDOE32-SGMC-CAL-v3.0` evaluates `62,703` off-catalogue USGS SGMC fault pixels).
- **How It Differs from Existing Repo Implementations:**
  - First pipeline across all 9 focus repos and sibling orgs to exploit the native horizontal gravity gradient vector `(Band 18, Band 11)` via exact Laplace-Harmonic divergence $-\partial^2 g/\partial z^2$ + Blakely-Simpson cross-contact inflection, combined with PU-safe collar-hardened Dual-Cover OOF (`89 ch` outside gap / `76 ch` inside the `24.63%` 1 m LiDAR gap) and a distance-balanced far-field structural spine floor.

---

### Rank 2 (`H-APART-2: CSTW-3`)
**Crustal Shear-Dilatation Tensor Eigen-Alignment + Microseismic Swarm Conduit Coupling (`transtensional_accommodation_bridge`)**
- **Exact Layers Used:** `Bands 4, 7, 8` (`geod_2ndinv`, `geod_shearrate`, `geod_dilaterate`) and `Bands 10, 16` (`deq_n100a15`, `ieq_n100a15`) coupled with gravity/magnetic/topographic strike azimuths.
- **Physical Signature:** Targets Walker Lane / Humboldt structural zone transtensional step-overs and accommodation zones (Faulds et al. 2011, 2021) where high shear-strain and dilatation invariants coincide with elevated microseismic swarm density (`log1p(Band 16) / log1p(Band 10 + 150 m)`).
- **Status:** Integrated as Channel 3 (`transtensional_accommodation_bridge`) of the 6-channel `BHGC` stack (`oriented AUC = 0.565243` on withheld faults).

---

### Rank 3 (`H-APART-3: MTCC-3`)
**Magnetotelluric Smectite-Illite Clay-Cap Lateral Gradient + Hydrothermal Demagnetization + 4-Block $^{214}\text{Bi}$ Radon & GDR #1391 Vent Plume (`hydrothermal_claycap_radon_vent`)**
- **Exact Layers Used:** `Band 17 (cond_surf)` lateral gradient (`cond_edge`), `spcp` hydrothermal demagnetization (`Bands 2, 3, 14`), 4-block standardized GeoDAWN $^{214}\text{Bi}$ radon (`10.5066/P93LGLVQ`), and GDR #1391 (`10.15121/1881483`) 2-m temperature probes & sinter vents.
- **Physical Signature:** Feeder faults breach the lateral margins of electrically conductive ($< 10\,\Omega\cdot\text{m}$) smectite clay caps (Cumming 2009; Wannamaker et al. 2007), creating coincident conductivity gradients, magnetite destruction, and $^{214}\text{Bi}$ radon / 2-m thermal anomalies.
- **Status:** Integrated as Channel 4 (`hydrothermal_claycap_radon_vent`) of the 6-channel `BHGC` stack (`oriented AUC = 0.545390` on withheld faults).

---

### Rank 4 (`H-APART-4: INSAR-3`)
**Multi-Temporal Sentinel-1 InSAR Line-of-Sight Velocity Gradient (`OPERA_L3_DISP-S1_V1`) & Nighttime ASTER Thermal Infrared (`AST_08`)**
- **Official Free Sources:** NASA ASF DAAC (`OPERA_L3_DISP-S1_V1`, 30 m) and USGS LP DAAC (`AST_08` Kinetic Temperature, 90 m).
- **Status:** Verified unobtainable inside the sandbox network firewall (allowlist permits only `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`). Documented with official URLs and deferred per protocol.

---

## 2. Pre-Registered 3-Experiment Ablation Plan (Protocol Rule 6)

1. **`EXP-1 (BHGC-Unsup-Spine)`:** Purely unsupervised 6-channel `BHGC` structural-geothermal crest spine (`bhgc_farfield_structural_spine` + visible-only tip/relay continuation) emitted at `K = 37,654, B = 2.0, d_min = 2.9 px`. Tests how much of both `GEMSDOE32-HIDE-RECOVER-v3.0` and `GEMSDOE32-SGMC-CAL-v3.0` is recovered by the physical Laplace-Harmonic gravity/magnetic/piedmont/vent spine alone without GBDT supervision.
2. **`EXP-2 (BHGC-OOF-Near)`:** PU-Safe Collar-Hardened 89-ch / 76-ch Dual-Cover `HistGradientBoostingClassifier` OOF posterior + local tip/relay continuation (`w_far_spine = 0.0`), emitted at `K = 37,654, B = 2.0, d_min = 2.9 px`. Tests the pure supervised Dual-Cover OOF gain from the 6 new `BHGC` channels and collar-hardened PU negative sampling.
3. **`EXP-3 (BHGC-BiPop-Full — Primary Candidate)`:** Full `H-APART-1 (BHGC-3)` Bi-Population fusion combining the 89-ch / 76-ch Dual-Cover OOF posterior, LLI-calibrated collar depletion attenuation (`2 < d_vis <= 4.5 px`), and distance-balanced far-field structural-geothermal spine floor (`w_far_spine = 0.28`), emitted via axial-crest greedy submodular CELF (`K = 37,654, B = 2.0, d_min = 2.9 px`).
   - **Promotion Gate:** Must simultaneously beat the `0.2778` Champion (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`) on:
     1. Pooled `GEMSDOE32-HIDE-RECOVER-v3.0` HOLDOUT-DTI (`> 0.099202`),
     2. Detached Blind Segments $\ge 600\text{ m}$ HOLDOUT-DTI (`> 0.094324`), and
     3. Untouched Off-Catalogue `GEMSDOE32-SGMC-CAL-v3.0` HOLDOUT-DTI (`> 0.064121`),
     while passing all 89 single-feature leakage canaries (`AUC <= 0.90`), all 582-raster uniqueness gates (`|Spearman| <= 0.90` and `<= 70%` 3-px overlap on genuine submissions), and strict GeoTIFF validation (`[0, 1]`, no NaN inside footprint, `EPSG:32611`).
