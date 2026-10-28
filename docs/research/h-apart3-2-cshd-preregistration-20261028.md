# Pre-Implementation Geological Hypotheses & Pre-Registration: `H-APART3-2 (CSHD)`

- **Repository / Branch:** `apartanish22-droid/ApartGEMSDOE3` (`arena/4d26cf27-apartgemsdoe3`)
- **Locked UTC Date:** `2026-10-28`
- **Method Lane:** **Crustal Seismogenic–Hydrothermal–Piedmont Dual-Cover (`CSHD`) Conduit Detection & Collar-Balanced Axial CELF Packing**
- **Experiment Budget Cap:** `<= 3` experiments (`E1`, `E2`, `E3`), `0` live portal uploads spent by automation
- **Uniqueness Gate:** Pre-placement continuous surface `|Spearman| <= 0.90` AND final emitted dots `<= 0.70` within `3 px` (`300 m`) against all `865` registry entries (`442` focus + `37` extra scored + `386` sibling-org/PR10 rasters + local `CFKC-DHC` `9dedadfc` + local `BHGC-3` `ab6646b7`).

---

## 1. Empirical Forensic Motivation Across 90+ Repos & 2026-10-27 Live Returns

Direct pixel-level measurement across `labels.tif` (`60,988` INGENIOUS Quaternary/Neogene fault pixels), off-catalogue `SGMC` bedrock faults (`62,703` pixels), and `111+` live-scored submissions (`0.0206` to `0.2778`) reveals why previous lanes underperformed or failed promotion gates:

1. **Range-Front Piedmont vs. Mountain-Core `SGMC` Mimic Dichotomy:**
   - `labels.tif` (`INGENIOUS` geothermal fault benchmark): median `det_elev_slope = 5.55°` (`q25 = 2.39°`, `q75 = 11.26°`, only `15.6% > 15°`), median `depth_to_base_surf = 321 m`, median `det_elev = -73.0 m`, median `iso_grav_anom_slope = 0.110`.
   - `SGMC` off-catalogue faults: median `det_elev_slope = 13.37°` (`43.3% > 15°`), median `depth_to_base_surf = 92 m`, median `det_elev = +127.1 m`, median `iso_grav_anom_slope = 0.087` (inactive Mesozoic/Paleozoic intrarange bedrock thrusts/contacts).
   - Consequence: `KANLERGEMSDOE2` (`0.1218` live despite `0.0789` local `SGMC-cal`) placed `47.6%` of its dots inside the depleted `2–6 px` catalogue collar and climbed onto `12.90°` mountain crests; conversely, `WBGGEMSDOE2` (`0.0262` live) and `WBGGEMSDOE3` (`0.0443` live) spilled `22.7%–26.6%` onto `< 2°` flat deep playas (`depth > 300 m`), and `ApartGEMSDOE1` (`0.0525` live) suffered `97.3%` 3-px dot clumping (`Clump>=3`).
   - Meanwhile, top live scorers (`GEMSDOE32`: `0.2778`, `GEMSDOE70`: `0.2478`, `GEMSDOE49`: `0.2376`, `GEMSDOE76`: `0.2343`, `GEMSDOE27 H31`: `0.2250`) consistently target range-front piedmont aprons and intrabasin horst/graben flanks (`slope_med = 7.5°–8.8°`, `d_cat > 15 px = 50%–58%`, `2 < d_cat <= 6 px = 18%–25%`, `flat_basin < 0.8%`, `Clump>=3 < 1%`).
2. **Prior Local Baseline Deficiencies (`BHGC-3` & `CFKC-DHC`):**
   - `BHGC-3` (`ab6646b7`) failed `src/gems32/release_gate.py::promotion_decision` because its paired bootstrap 95% CI vs. the `0.2778` Champion spanned zero (`[-0.00466, +0.00980]` on `HIDE-RECOVER-v3.0`, `[-0.00091, +0.01452]` on `SGMC-CAL-v3.0`), lost `Censored d_hid > 2 px` (`0.00380 < 0.00452`), spilled `3.74%` into flat deep playas via an uncalibrated `np.maximum(oof_term, far_term)` override, lacked seamless 10 m USGS 3DEP DEM / fluvial $\chi$ inside the `24.63%` 1 m LiDAR gap, and sat at `69.31%` 3-px overlap with `H48-1`.

---

## 2. Five Pre-Registered Untried Geological Hypotheses (Ranked by Expected DTI Lift & Cost)

### Rank 1 — `H-APART3-2A` (`CSHD-Seis`): Sub-km USGS ANSS ComCat Brittle-Geothermal Hypocentral Swarms & Post-2021 Fault-Strike Lineament Bridges
- **Exact Layers & Official Free External Sources:**
  - Official USGS Earthquake Hazards Program ANSS ComCat FDSN Event Web Service v1 (`external/usgs_comcat_geodawn.csv`, `sha256: c580226b...`, verified by `usgs_comcat_provenance.json`, `Public Domain 17 U.S.C. 105 / CC0`, <https://earthquake.usgs.gov/fdsnws/event/1/query>): `3,977` deduplicated `1900–2026` events (`2,040` inside valid GeoDAWN footprint, including **`541` modern post-2021 events recorded after the 2021 GDR #1391 fault compilation cutoff**);
  - Official competition `Band 10` (`deq_n100a15`) and `Band 16` (`ieq_n100a15`).
- **Physical Signature / Transform:**
  1. `comcat_brittle_hypocenter_density`: Magnitude-weighted ($1 + 0.5\max(M - 2, 0)$) and brittle-geothermal-window depth-weighted ($\exp[-((z - 6.5\text{ km})/5.5\text{ km})^2]$) multi-scale (`400 m`, `1.2 km`, `3.0 km`) hypocentral kernel density;
  2. `comcat_post2021_lineament_bridge`: Post-2021 reactivation swarm excess fused with an 8-azimuth directional Radon/oriented Gaussian chord filter ($\sigma_\parallel = 9\text{ px}, \sigma_\perp = 1.6\text{ px}$) bridging discrete microseismic epicenters along active fault strike beneath Holocene cover.
- **Why It Catches Faults Missing from USGS/INGENIOUS:** Official `Bands 10, 16` are smooth `100`-nearest-event regional fields frozen $\le 2021$ that erase sub-km fault-zone lineaments and omit `541` 2021–2026 earthquakes. Active blind step-overs, accommodation zones, and nascent geothermal swarms rupture microseismically at `2–12 km` depth beneath unscarped alluvial basins.
- **Difference vs. Repo Implementations:** Completely untried in `ApartGEMSDOE3` (`features.py`, `spcp.py`, `trhv.py`, `ldgi.py`, `fbgr.py`, `bhgc.py`, `cfkc.py` contain zero ComCat hypocenter point-cloud or post-2021 seismic features).
- **Expected DTI Lift / Cost:** High (`+0.004` to `+0.008` HOLDOUT-DTI; strong blind off-network transfer) / Low cost (`< 3 s` CPU).

### Rank 2 — `H-APART3-2B` (`CSHD-Chem`): Blind Hydrothermal Chemical Geothermometer Disequilibrium ($\Delta T_{\text{SiO}_2/\text{Na-K-Ca}}$) & Conductive-Clay-Cap Coupling
- **Exact Layers & Official Free External Sources:**
  - Official DOE Geothermal Data Repository Submission #1391 Well & Spring Temperature and Chemistry (`external/gdr_wellspring_in_footprint.csv`, DOI `10.15121/1881483`, `CC BY 4.0`, <https://gdr.openei.org/submissions/1391>; column `dist_known_fault_px` strictly dropped on load): `temp_c`, `geothermquartz_c`, `geothermchalc_c`, `geothermcat_c`;
  - Official DOE GDR #1391 2-m shallow temperature probes (`2m_temperature_probe_INGENIOUS_regional_data.zip`, `2,782` in-footprint stations) and paleo-geothermal sinters/tufas (`paleo_geothermal_regional.zip`, `281` vents);
  - Official competition `Band 17` (`cond_surf` electrical conductivity) and `fbgr` 4-block contractor-normalized $^{214}\text{Bi}/^{232}\text{Th}$ radon-fault soil-gas excess.
- **Physical Signature / Transform:**
  1. `gdr_blind_geotherm_disequilibrium`: Fournier (1977) silica & Fournier-Truesdell (1973) cation chemical geothermometer thermal disequilibrium $\Delta T_{\text{diseq}} = \max(T_{\text{quartz}}, T_{\text{chalcedony}}, T_{\text{Na-K-Ca}}) - T_{\text{discharge}}$, specifically isolating the **`653` blind cold/tepid-outflow wells & springs** (`T_surf < 45°C`, `T_geotherm > 85°C`, median $\Delta T_{\text{diseq}} = +87.4^\circ\text{C}$) where deep `120–220°C` fault-hosted fluids ascend through hidden permeable fault damage zones and cool conductively before reaching the water table;
  2. `cond_radon_upflow_gradient`: Lateral gradient and ridge curvature of `Band 17` (`cond_surf` hydrothermal smectite clay-cap boundary) multiplicatively coupled with $\Delta T_{\text{diseq}}$, 2-m thermal probes, and block-normalized $^{214}\text{Bi}$ fault-gas leakage.
- **Why It Catches Faults Missing from USGS/INGENIOUS:** Boiling hot springs (`temp_c > 70°C`) with surface sinter terraces were mapped into `labels.tif`; blind geothermal systems (~75% of Great Basin undiscovered resources; Coolbaugh et al. 2006, Faulds & Hinz 2015) lack boiling surface discharge and surface scarps, leaving chemical geothermometer disequilibrium in cool agricultural/stock wells as their primary geochemical signature.
- **Difference vs. Repo Implementations:** `spcp.py` only computed `max(temp_c, geotherm*) - 45°C`, conflating mapped hot springs with blind cold-discharge upflow plumes and never computing $\Delta T_{\text{diseq}} = T_{\text{geotherm}} - T_{\text{discharge}}$.
- **Expected DTI Lift / Cost:** Medium-High (`+0.003` to `+0.006` HOLDOUT-DTI) / Very Low cost (`< 2 s` CPU).

### Rank 3 — `H-APART3-2C` (`CSHD-PiedChi`): Seamless 10 m USGS 3DEP Piedmont Apron Break-in-Slope & Valley-Exit Fluvial $\chi$-Gravity Concordance
- **Exact Layers & Official Free External Sources:**
  - Restored USGS 3DEP 1/3 arc-second (`~10 m`) seamless DEM derivatives (`external/topo_10m_derived_100m_u8.tif`: `slope_p90`, `curv_prof_absmax`, `aspect_coherence`, `hs_lineament`; `100.0%` valid coverage across all `5,167,373` footprint pixels including the `24.63%` 1 m LiDAR gap; `U.S. Public Domain`, <https://www.usgs.gov/3d-elevation-program>);
  - Restored USGS 3DEP 10 m Perron-Royden (2013) fluvial $\chi$ & channel steepness derivatives (`external/dem10_chi_100m_i16.tif`: `step_max_x1000`, `ksn_max_m0.9`; `external/dem10_chi_100m_u8.tif`: `knick_n`, `raised_n`; `U.S. Public Domain`);
  - Official competition `Band 12` (`det_elev`), `Band 15` (`depth_to_base_surf`), `Band 19` (`det_elev_slope`), `Band 05` (`iso_grav_anom_slope`), `Band 13` (`iso_grav_anom`), and Laplace harmonic gravity divergence (`bhgc` ch 0).
- **Physical Signature / Transform:**
  1. `seamless_10m_piedmont_apron_scarp`: 10 m seamless profile-curvature × aspect-coherence × hillshade-lineament crest (`topo_10m_derived_100m_u8.tif` bands 6, 7, 8) weighted by the empirical INGENIOUS range-front piedmont envelope ($G_{\text{pied}} = \sigma((\text{slope} - 1.6^\circ)/0.9^\circ)\cdot\exp[-\max(\text{slope} - 13.5^\circ, 0)^2 / 64]$) and Lake Lahontan (`~1,332 m`) shoreline-vetoed — providing `100%` seamless scarp resolution across the `24.63%` 1 m LiDAR gap;
  2. `piedmont_chi_gravity_concordance`: Fluvial $\chi$-step jump (`step_max_x1000`) × normalized channel steepness (`ksn_max_m0.9`) × tributary knickpoint density (`knick_n`) gated strictly to piedmont range-front transitions (`1.8° <= slope <= 14.5°`, `depth_to_base >= 40 m`, suppressing `SGMC`-style high-mountain drainage-divide $\chi$ mimics!) and geometrically concordant with Laplace-harmonic basement gravity gradient (`bhgc` ch 0 + `fbgr` FFT upward-continued gravity).
- **Why It Catches Faults Missing from USGS/INGENIOUS:** Degraded `< 1.5 m` Holocene alluvial-fan scarps and all faults inside the `24.63%` (`1,274,189` px) 1 m LiDAR hole were systematically under-mapped in aerial-photo Quaternary compilations, yet leave coherent 10 m 3DEP profile-curvature breaks and footwall-uplift $\chi$ knickzones directly over basement-offset gravity gradients.
- **Difference vs. Repo Implementations:** `BHGC-3` (`main`) lacked `topo_10m_derived_100m_u8.tif` and `dem10_chi_100m` entirely; `CFKC-DHC` used raw un-gated $\chi$ jumps that fired on steep mountain drainage divides (`slope_med = 10.83°`).
- **Expected DTI Lift / Cost:** High (`+0.005` to `+0.010` HOLDOUT-DTI, especially inside the `24.63%` LiDAR gap) / Low cost (`< 6 s` CPU).

### Rank 4 — `H-APART3-2D` (`CSHD-Strain`): Geodetic Strain-Tensor Kinematic Partitioning ($\psi_\varepsilon$) & Locking-Transition Reactivation Gradient
- **Exact Layers:** Official competition geodetic strain-rate tensor invariants `Band 04` (`geod_2ndinv`), `Band 07` (`geod_shearrate` $\dot{\gamma}$), `Band 08` (`geod_dilaterate` $\dot{\Delta}$), coupled with local structural strike azimuth $\theta_{\text{struct}}$ from seamless 10 m 3DEP scarp / gravity horizontal gradients (`Bands 12, 13, 18`).
- **Physical Signature / Transform:**
  - `strain_kinematic_reactivation_index`: Transtensional dilation-to-shear kinematic regime index $\psi_\varepsilon = \arctan2(\dot{\Delta}, \dot{\gamma} + \epsilon)$ (separating pure normal extension in central/northern Nevada grabens from dextral-transtensional shear in the Walker Lane) + spatial strain-rate locking gradient $|\nabla_h \dot{\gamma}| + |\nabla_h \dot{\Delta}|$, weighted by structural strike coherence (Morris, Ferrill & Henderson 1996 critical dilation/slip tendency).
- **Why It Catches Faults Missing from USGS/INGENIOUS:** Separates critically stressed, actively dilating Quaternary geothermal conduits (which maintain fracture permeability against silica self-sealing) from inactive Mesozoic `SGMC` thrusts and erosional scarps.
- **Difference vs. Repo Implementations:** `features.py` passed raw `Bands 4, 7, 8` with zero kinematic regime ratio $\arctan2(\dot{\Delta}, \dot{\gamma})$ or spatial strain-locking gradient (`IR-32-BAND-01`).
- **Expected DTI Lift / Cost:** Medium (`+0.002` to `+0.005` HOLDOUT-DTI) / Very Low cost (`< 3 s` CPU).

### Rank 5 — `H-APART3-2E` (`Reserve`): Multi-Depth 3D Magnetotelluric–Gravity Wavelet Phase Coherence
- **Exact Layers:** Multi-scale wavelet cross-phase coherence between `Band 17` (`cond_surf`) and multi-altitude upward-continued Bouguer/isostatic gravity (`Band 13`) across `2–8 km` wavelengths.
- **Status:** Held in reserve outside the 3-experiment budget (`<= 3` experiments rule) because `Band 17` horizontal station spacing (~15 km) has coarser lateral localization than the `300 m` DTI kernel; its clay-cap upflow edge is already incorporated inside `H-APART3-2B`.

---

## 3. Named Non-Fault Mimic Processes & Explicit Physical Suppression

1. **Mesozoic/Paleozoic Intrarange Bedrock Thrusts & Drainage-Divide $\chi$ Jumps (`SGMC` Mountain-Core Mimic):** High relief and $\chi$ asymmetry at `slope > 15°`, `depth_to_base < 80 m`, `det_elev > +120 m` with weak Cenozoic gravity offset (`KANLER2: 0.1218` failure mode). Suppressed by the INGENIOUS piedmont-apron envelope $G_{\text{pied}}$ and harmonic basement-gravity concordance.
2. **Closed-Basin Desert Playa Desiccation Polygons, Salt Flats & Pluvial Lake Lahontan (`~1,332 m`) Shorelines:** Produce radiometric K/U evaporite highs, conductive clay pans (`Band 17`), and horizontal contour benches (`WBG2: 0.0262`, `WBG3: 0.0443` failure modes). Suppressed by flat deep playa veto (`depth_to_base > 300 m & slope < 2.0°`), Lahontan contour veto (`trhv` ch 5), and multiplicative OOF probability anchoring (replacing `BHGC-3`'s uncalibrated `np.maximum` far-basin override).
3. **Anthropogenic Highway/Railroad Prisms & Open-Pit Mine Benches:** Produce sharp 1 m / 10 m DEM breaks (`IR-32-VERIFY`). Suppressed by US Census TIGER/Line 150 m road prism weight (`trhv` ch 4) and US BLM MLRS mining-scar damping (`fbgr` ch 10).

---

## 4. Pre-Registered 3-Experiment Factorial Ladder (`<= 3` Experiments)

All three arms emit **matched `37,654` binary `{0.0, 1.0}` dots** strictly outside `B = 2 px` (`200 m`) of the fold-visible (`OOF`) or full (`submission`) fault catalogue (`existing_faults.tif`), evaluated identically on `GEMSDOE32-HIDE-RECOVER-v3.0` (`n = 22,232` withheld positives across 4 spatially blocked 1.5 km-collared quadrants), `Detached >= 600 m` (`n = 15,504`), `Censored d_hid > 2 px`, and `GEMSDOE32-SGMC-CAL-v3.0` (`n = 62,703`):

- **`EXP-1` (`CSHD-Unsup-Crest`):** Pure zero-label unsupervised physical `CSHD` crest spine (`ch 7`: ComCat hypocentral lineaments + GDR #1391 blind $\Delta T_{\text{diseq}}$ + 10 m 3DEP piedmont-$\chi$ / harmonic gravity + geodetic $\psi_\varepsilon$), packed via `gems32.emitter.emit(..., min_sep_px=3.24)`. Tests standalone geological physics without supervision.
- **`EXP-2` (`CSHD-SingleCover-97ch`):** 4-quadrant 1.5 km-collared OOF `HistGradientBoosting` ensemble over all `97` channels (`89` prior + `8` new `CSHD` channels) as a single classifier without Dual-Cover `LiDAR-valid` / `LiDAR-gap` stationary split or physical crest-carrier anchoring (`min_sep_px=3.24`). Tests supervised lift vs. `EXP-1` while measuring single-cover LiDAR-gap attenuation.
- **`EXP-3` (`H-APART3-2: CSHD-DualCover-Axial324` — Pre-registered Primary Candidate):** Stationary Dual-Cover OOF (`97`-ch `M_Full` inside `75.37%` 1 m LiDAR + quantile-calibrated strictly 1 m LiDAR-free `84`-ch `M_Gap` inside `24.63%` 1 m LiDAR gap) multiplicatively fused with the physical `CSHD` seismogenic-geothermal piedmont crest carrier, collar-balanced relay coupling (`d_vis > 2 px`), and 1-px oriented probability crest sharpening, packed via `gems32.emitter.emit(..., min_sep_px=3.24)` (`Clump>=3 = 0.00%`).

**Strict Promotion Criteria (`release_gate.promotion_decision`):**
1. Single-feature leakage canary `AUC <= 0.90` across all `97` channels;
2. Pre-placement surface uniqueness `|Spearman| <= 0.90` AND final emitted dots `3-px overlap <= 0.70` across all genuine registry submissions (including `9dedadfc`, `ab6646b7`, and `db09cca5`);
3. Paired cluster-bootstrap 95% CI strictly `> 0.0` vs. the `0.2778` Champion (`e5eb6e7e`) on **BOTH** `GEMSDOE32-HIDE-RECOVER-v3.0` AND `GEMSDOE32-SGMC-CAL-v3.0`, plus positive lift on `Detached >= 600 m` and `Censored d_hid > 2 px`;
4. Zero NaNs (`12,279,160 / 12,279,160` finite `float32`), values strictly in `[0.0, 1.0]`, `nodata=None`, exact template CRS/shape/transform (`check_submission.py` PASS).
