# Pre-Implementation Preregistration — `H-APART3-3` (`WCHD`: Harmonic Upward-Continuation Listric Contact-Dip Updip Projection, Repaired True-RTP Magnetic Tilt Phase, Hydrothermal Magnetite-Destruction × Adularia K/eTh Metasomatism & Stress-Resolved Dilation-Tendency Dual-Cover Detection)

- **Date (UTC):** `2026-10-28`
- **Repository:** `apartanish22-droid/ApartGEMSDOE3`
- **Active Session Branch:** `arena/19877ca7-apartgemsdoe3` (branched from `cbce0ab6375e148eeb03e3d3e0513b01af288e51`)
- **Protocol Budget:** Strictly `<= 3` holdout experiments (`EXP-1`, `EXP-2`, `EXP-3`), `<= 2` hours wall-clock, `0` live DrivenData portal slots consumed (`slot_used = false`, `selector_required = true`).
- **Pre-Implementation Status:** Written and locked **before** implementing `src/gems32/wchd.py` or running any `H-APART3-3` holdout experiment.

---

## 1. Forensic Audit of Open Next Steps & Irregularities Addressed in This Session

1. **Prior Submission Non-Duplication (`37b32d5b` & `9dedadfc`):** Both `cfkc-dhc-37654-20261027T215000Z-9dedadfc` and `apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros` now appear in the cross-session submission ledger. Therefore `H-APART3-3` must emit a brand-new, physically orthogonal `.tif` that satisfies **both** Step A (`|Spearman| <= 0.90` continuous surface) and Step B (`<= 0.70` 3-px dot overlap) against **every** genuine discrete registry raster—explicitly including `37b32d5b` (`CSHD`), `ab6646b7` (`BHGC-3`), `9dedadfc` (`CFKC-DHC`), `5d4d0085` (`CTHG-DHC`), `e5eb6e7e` (`GEMSDOE32` `0.2778` Champion), `0d4e02e8` (`GEMSDOE23`), and all newly refreshed `2026-10-28` peer rasters (`1,033` total manifest entries across focus, extra-scored, and sibling repos).
2. **Sibling Registry Typo Repaired (`sassasfras46-hue` -> `sassnarep3-star` + `swgb/` prefix):** Verified via `git ls-remote` that `sassnarep3-star/GEMSDOESASS1..3` are live (`7f87fc64`, `3b21e4e9`, `86874b72`), including `swgb/downloads/gemsass1-swgb-hrv2-44090dots-20261027T122104Z-f9b3f764-zeros.tif`. Patched `scripts/restore_pinned_registry.py` and refreshed all `471` focus rasters + `37` extra-scored rasters + `525` sibling-org rasters.
3. **Complete Elimination of `Band 6 (tc)` Magnetic-Tilt Misidentification (`IR-A8A-BAND6-TC-01` / `IR-CTHG-BAND6-TC-02` / `IR-WCHD-BAND6-DROP-01`):** Although PR #18 documented `IR-CTHG-BAND6-TC-02`, `CSHD` still included `bhgc_extra_6ch.npy` ch 1 (global column `84`) inside its 97-channel supervised matrix, and `bhgc` ch 1 treated `Band 6 (tc)` (GeoDAWN radiometric Total Count, `r = +0.9971`) as magnetic tilt. In `H-APART3-3`, **global column `84` (`bhgc` ch 1) is strictly excised** from all supervised feature matrices and replaced by exact 2-D Fourier vertical-derivative Reduced-to-Pole magnetic tilt on `Band 2 (rtp)` corroborated by organizer `Band 3 (tmi_hg)` and `Band 9 (tmi_vg)` (`r = +0.9877` with $\|\nabla_h \text{TMI}\|$ and `r = +0.9323` with Fourier $\partial \text{TMI}/\partial z$).

---

## 2. Five Untried Candidate Geological Hypotheses (Pre-Implementation Design & Ranking)

### Hypothesis 1 (Rank #1 — SELECTED LANE): `H-APART3-3 (WCHD)` — *Harmonic Upward-Continuation Listric Contact-Dip Updip Projection, True-RTP Magnetic Tilt Wall, Hydrothermal Magnetite-Destruction × Adularia K/eTh Metasomatism & Stress-Resolved Dilation-Tendency Dual-Cover Detection*

- **Specific Layers Involved:**
  - `training_features.tif` `Band 13` (`iso_grav_anom`), `Band 5` (`iso_grav_anom_slope`), `Band 18` (`iso_grav_anom_hg`), `Band 11` (`iso_grav_anom_vg`), `Band 15` (`depth_to_base_surf`);
  - `Band 2` (`rtp` reduced-to-pole magnetic anomaly), `Band 3` (`tmi_hg`), `Band 9` (`tmi_vg`);
  - `Band 17` (`cond_surf`), `Bands 4, 7, 8` (`geod_2ndinv`, `geod_shearrate`, `geod_dilaterate`), `Bands 12, 19` (`det_elev`, `det_elev_slope`);
  - Official USGS GeoDAWN gamma-ray spectrometry (`external/geodawn_rad_u8.tif`: `K`, `Th`, `U`, `TC` per contractor block `external/acquisition_block_id_100m.tif`, DOI `10.5066/P93LGLVQ`);
  - Official USGS 3DEP 10 m seamless DEM & fluvial $\chi$ (`external/topo_10m_derived_100m_u8.tif`, `external/dem10_chi_100m_i16.tif`), USGS ANSS ComCat (`external/usgs_comcat_geodawn.csv`), and DOE GDR #1391 (`external/gdr_wellspring_in_footprint.csv`, `dist_known_fault_px` dropped).
- **Physical Signature & Mathematical Transform Targeted (`8` strictly label-free, 100% 1 m LiDAR-free channels):**
  1. `wchd_ch0 — true_rtp_tmi_tilt_contact_wall`: Exact 2-D Fourier vertical derivative $\partial M_{\text{RTP}}/\partial z = \mathcal{F}^{-1}[2\pi |\mathbf{k}| \mathcal{F}(M_{\text{RTP}})]$ and horizontal gradient $\|\nabla_h M_{\text{RTP}}\|$ on `Band 2 (rtp)` fused with organizer `Band 9 / Band 3` TMI tilt, extracting the Miller & Singh (1994) zero-crossing wall $\operatorname{sech}^2(\theta_{\text{mag}}/0.38)\cdot \sqrt{\|\nabla_h M_{\text{RTP}}\|}$.
  2. `wchd_ch1 — poisson_listric_updip_trace`: 4-altitude Poisson upward continuation $g(x,y,z) = \mathcal{F}^{-1}[e^{-2\pi |\mathbf{k}| z}\mathcal{F}(g_0)]$ at $z \in \{200, 600, 1500, 3000\}\text{ m}$ on `Band 13 (iso_grav_anom)`. For a Basin-and-Range normal fault dipping at $\delta \in [45^\circ, 65^\circ]$ basinward, the horizontal-gradient crest $\|\nabla_h g(z)\|$ migrates downdip into the hanging wall by $\Delta x(z) \approx z \cot \delta$. Advecting deep ($z = 1500, 3000\text{ m}$) hanging-wall gravity-gradient roots **updip** along the unit footwall-pointing vector $-\nabla_h D_{\text{base}}/\|\nabla_h D_{\text{base}}\|$ back to $z \to 0$ recovers the **concealed sub-alluvial surface fault trace** while rejecting vertical volcanic dikes ($\Delta x(z) = 0$) and shallow boulder fans ($g(3000\text{ m}) \to 0$).
  3. `wchd_ch2 — joint_grav_rtp_phase_congruency`: Multi-altitude Kovesi/Cooper-Cowan phase congruency $\cos^2(\psi_g - \psi_{\text{RTP}})\cdot \operatorname{sech}^2(\theta_g/0.40)\cdot \operatorname{sech}^2(\theta_{\text{RTP}}/0.42)$ across $z \in \{200, 1000\}\text{ m}$, isolating crustal faults that offset both density and magnetic susceptibility basement blocks.
  4. `wchd_ch3 — hydro_demag_kth_adularia_corridor`: Hydrothermal **magnetite-destruction trough** (band-pass positive Laplacian $\nabla_h^2 M_{\text{RTP}} > 0$ where sulfidizing/argillic geothermal fluids convert ferrimagnetic titanomagnetite into non-magnetic pyrite/illite/chlorite along permeable fault cores) coupled with **4-contractor-debiased potassium/thorium metasomatism excess** ($Z_{\text{block}}(K) - 0.75\,Z_{\text{block}}(\text{Th})$) and `Band 17` MT clay-cap lateral gradients, damped on closed playas.
  5. `wchd_ch4 — morris_dilation_slip_tendency`: Resolves Great Basin WNW–ESE minimum horizontal stress ($S_{h\min} \approx \text{N}114^\circ\text{E}$, locally modulated by geodetic strain `Bands 7, 8`) onto the local multi-physics fault strike tangent $\hat{\mathbf{t}}(\mathbf{x})$, scoring normalized dilation tendency $T_d = \cos^2(\alpha_n)$ plus Walker Lane transtensional slip tendency $T_s = \sin(2\alpha_n)$.
  6. `wchd_ch5 — horst_cross_divide_tilt_footwall`: Pairs 10 m 3DEP headwater drainage-divide $\chi$ contrast (`dem10_chi_100m_i16.tif`) with `3.5 km` vs `0.5 km` cross-range `det_elev` tilt asymmetry and piedmont break-in-slope curvature (`1.7° <= slope <= 13.8°`), localizing the active range-front normal fault on asymmetrically tilting horsts.
  7. `wchd_ch6 — updip_blind_geotherm_seismic_bridge`: Strike-aligned coupling of `wchd_ch1` updip-projected basement fault traces and `wchd_ch3` magnetite-destruction corridors with blind cold-spring silica/cation geothermometer disequilibrium (`gdr_wellspring_in_footprint.csv`) and post-2021 ComCat lineaments.
  8. `wchd_ch7 — wchd_unified_updip_conduit_crest`: Oriented 1-px Hessian crest-thinned WCHD structural-geothermal spine vetoed for Lake Lahontan paleoshorelines (`1325–1342 m`, `1268–1284 m`), TIGER road cuts, BLM mining disturbances, and flat playa interiors.
- **Why It Catches Faults Missing from USGS/INGENIOUS:**
  - Mapped Quaternary faults (`labels.tif`) are heavily concentrated on exposed Holocene range-front scarps inside 1 m LiDAR coverage. Hidden faults and blind geothermal conduits occur (a) **150–600 m basinward under active alluvial aprons** where fan progradation buried the surface scarp, yet listric basement throw produces systematic downdip gravity-crest migration across $z \in \{200..3000\}\text{ m}$ whose updip projection recovers the concealed surface trace; (b) **inside hydrothermally altered volcanic/intrusive corridors** where magnetite destruction + K/eTh adularia metasomatism reveal fluid-transmitting damage zones without fresh topographic scarps; and (c) **inside the `24.63%` 1 m LiDAR coverage gap** where 100% non-LiDAR `WCHD` channels preserve sharp structural localization.
- **Named Non-Fault Mimic Processes Explicitly Suppressed:**
  1. Vertical Miocene/Oligocene basaltic feeder dikes and ash-flow caldera margins (strong magnetic/gravity edges, zero downdip migration $\Delta x(z) \approx 0$ across $z \in \{200..3000\}\text{ m}$).
  2. Closed evaporite playa clay-pan centers (`depth_to_base > 300 m, slope < 2.0 deg` high K/illite + high `cond_surf` without dipping basement step).
  3. Primary unaltered felsic rhyolite domes (high `%K` accompanied by proportionally high `eTh`, cancelled by $Z_{\text{block}}(K) - 0.75\,Z_{\text{block}}(\text{Th})$) and GeoDAWN contractor flight-block boundary seams.
  4. Lake Lahontan wave-cut shorelines (`1325–1342 m`, `1268–1284 m`), TIGER highway embankments, and BLM open-pit mine benches.
- **How It Differs from Existing `ApartGEMSDOE3` Implementations:**
  - Excises `BHGC` ch 1 (`Band 6` radiometric TC pseudo-tilt) from all supervised learners and replaces it with exact Fourier RTP + organizer TMI tilt (`wchd_ch0`, `wchd_ch2`).
  - Replaces `FBGR`'s 2-level isotropic upward-continuation difference with a **4-altitude ($200, 600, 1500, 3000\text{ m}$) downdip-to-updip vector advection** onto the concealed sub-alluvial fault apex (`wchd_ch1`).
  - Replaces `CSHD`'s point-source radial spring/earthquake blind carrier with a **continuous linear updip-trace + magnetite-destruction/K-eTh metasomatism + Subspace OOF (`M_Subspace`)** carrier and `min_sep_px = 4.02` axial dispersion, ensuring `<= 0.70` 3-px overlap against `CSHD` (`37b32d5b`) as well as all other genuine registry rasters.

---

### Hypothesis 2 (Rank #2): `H-APART3-3B (K3PC)` — *Standalone 4-Contractor Radiometric K/eTh/eU Alteration & Magnetite-Destruction Classifier*
- **Layers:** `external/geodawn_rad_u8.tif`, `external/acquisition_block_id_100m.tif`, `Band 2 (rtp)`, `Band 17 (cond_surf)`.
- **Transform:** Block-wise MAD standardization of `(K, Th, U)` + RTP Laplacian trough.
- **Why Unmapped & Difference:** Targets self-sealed adularia-illite geothermal outflow aprons lacking Holocene scarps. Standalone gamma-ray penetration is ~30 cm, so absorbed as `wchd_ch3` rather than deployed solo.

### Hypothesis 3 (Rank #3): `H-APART3-3C (CDCA)` — *Cross-Divide Gilbert Headwater $\chi$-Asymmetry & Horst Footwall Tilt*
- **Layers:** `external/dem10_chi_100m_i16.tif`, `external/topo_10m_derived_100m_u8.tif`, `Band 12 (det_elev)`.
- **Transform:** Across-divide $\Delta\chi$ paired with `3.5 km` horst tilt vector pointing to the active range-front piedmont break.
- **Why Unmapped & Difference:** Identifies which side of an asymmetric horst hosts the active Quaternary bounding fault even where alluvial fans bury the scarp; integrated as `wchd_ch5`.

### Hypothesis 4 (Rank #4): `H-APART3-3D (SSTE)` — *Geodetic-Modulated Morris Dilation & Transtensional Slip Tendency*
- **Layers:** `Bands 4, 7, 8` (`geod_*`), `Band 13`, `external/topo_10m_derived_100m_u8.tif`.
- **Transform:** $T_d = \cos^2(\alpha_n)$ and $T_s = \sin(2\alpha_n)$ under $S_{h\min} = \text{N}114^\circ\text{E}$ locally rotated by GPS strain eigenvectors.
- **Why Unmapped & Difference:** Separates critically stressed fluid-transmitting NNE/ENE conduits from sealed E–W Mesozoic thrusts; integrated as `wchd_ch4`.

### Hypothesis 5 (Rank #5 — Deferred External Obtainability Check): `H-APART3-3E (ARIA-InSAR)` — *NASA/JPL ARIA Sentinel-1 Aquifer-Barrier Phase Gradient*
- **Official Free Source:** NASA/JPL ARIA Gunw Standard Displacement Products (`https://aria-share.jpl.nasa.gov/`, `https://asf.alaska.edu/datasets/daac/aria-sentinel-1-gunw/`).
- **Obtainability Verification:** Not mirrored in `registry/data_manifest.json` and external hosts (`aria-share.jpl.nasa.gov`, `asf.alaska.edu`) are outside the sandbox outbound allowlist (`github.com`, `codeload.github.com`, `api.github.com`, `pypi.org`, `registry.npmjs.org`). Documented as a concrete next-session data-mirror addition rather than fabricated.

---

### Pre-Implementation Ranking Table

| Rank | ID | Geological Hypothesis | Obtainable Now? | Expected `HOLDOUT-DTI` Lift vs `0.2778` | Compute Cost | Decision |
|---:|---|---|:---:|---|---|---|
| **1** | **`H-APART3-3 (WCHD)`** | 4-altitude Poisson contact-dip updip projection + repaired true-RTP magnetic tilt + magnetite-destruction × K/eTh adularia + Morris dilation + Dual-Cover/Subspace OOF | **Yes (100% SHA-256 verified)** | **`+0.008` to `+0.013`** on `v3.0` & `SGMC-CAL-v3.0`, positive on `Detached >= 600 m` | Moderate (~10 min, `< 1.5 GiB` RSS) | **EXECUTE (`EXP-1..3`)** |
| **2** | `H-APART3-3B (K3PC)` | Contractor-debiased K/eTh metasomatism × RTP magnetite-destruction | Yes | `+0.003` solo | Low | Integrated as `wchd_ch3` |
| **3** | `H-APART3-3C (CDCA)` | Cross-divide $\chi$ asymmetry + horst tilt footwall localization | Yes | `+0.002` solo | Low | Integrated as `wchd_ch5` |
| **4** | `H-APART3-3D (SSTE)` | Geodetic-modulated Morris dilation & slip tendency | Yes | `+0.002` solo | Low | Integrated as `wchd_ch4` |
| **5** | `H-APART3-3E (ARIA-InSAR)` | Sentinel-1 ARIA vertical phase gradient across unmapped aquifer barriers | Deferred (not in manifest / sandbox allowlist) | `+0.004` to `+0.008` once mirrored | High | Defer to next data-mirror PR |

---

## 3. Strict Pre-Registered 3-Experiment Ladder & Gates

1. **Step 0 — 100%-Channel Leakage Canary (`AUC <= 0.90`):** Test all `104` clean features (`96` clean prior channels with `bhgc` ch 1 excised + `8` new `WCHD` channels) individually on `GEMSDOE32-HIDE-RECOVER-v3.0` (`n = 22,232` withheld positives). Hard abort if any single channel has `AUC > 0.90`.
2. **`EXP-1` (`EXP1_WCHD_UNSUP_UPDIP`):** Zero-label physical `WCHD` updip contact-dip & hydrothermal magnetite-destruction crest spine (`wchd_ch7`) + fold-visible relay (`K = 37,654`, `B = 2.0 px`, `min_sep_px = 4.02`).
3. **`EXP-2` (`EXP2_WCHD_SINGLE104_OOF`):** Clean 104-channel Single-Cover OOF ensemble (`bhgc` ch 1 excised) without Dual-Cover `LiDAR-valid / LiDAR-gap` routing or `WCHD` updip-subspace two-population envelope (`K = 37,654`, `B = 2.0 px`, `min_sep_px = 4.02`).
4. **`EXP-3` (`EXP3_WCHD_DUAL104_UPDIP_FULL` — Primary Pre-Registered Candidate):** Clean **104-ch `M_Full` / 91-ch `M_Gap` Stationary Dual-Cover OOF** + **34-ch Potential-Field/Alteration/Updip Subspace OOF (`M_Subspace`)** + **`WCHD` Updip Blind-Conduit Two-Population Envelope** (`K = 37,654`, `B = 2.0 px`, `min_sep_px = 4.02`).
5. **Fail-Closed Promotion Gate:**
   - Beats `0.2778` Champion (`e5eb6e7e`) on `GEMSDOE32-HIDE-RECOVER-v3.0` (`n = 22,232`) AND `GEMSDOE32-SGMC-CAL-v3.0` (`n = 62,703`) with **paired bootstrap 95% CI strictly `> 0`**, and beats `0.2778` Champion (`0.094324`) on `Detached >= 600 m` (`n = 15,504`).
   - Passes **Step A** (`|Spearman| <= 0.90` continuous pre-placement surface) and **Step B** (`<= 0.70` 3-px dot overlap) across **all** genuine discrete registry rasters (`<= 100,000` dots), explicitly including `37b32d5b`, `ab6646b7`, `9dedadfc`, `5d4d0085`, `e5eb6e7e`, `0d4e02e8`, and all newly refreshed sibling-org rasters.
   - Passes `scripts/check_submission.py --strict-finite` (`12,279,160` finite `float32` pixels in `[0.0, 1.0]`, `0` NaN, `0` Inf, `EPSG:32611`, `3730 x 3292`).
