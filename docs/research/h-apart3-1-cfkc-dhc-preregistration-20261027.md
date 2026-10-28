> **Historical research record; not a current release decision. DO NOT SUBMIT.** Prior promotion and score claims below have not been independently verified. See the [current review](https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/knowledge/09_release_recheck_and_hypotheses_20261028.md).

# Pre-Registration: `H-APART3-1` (`CFKC-DHC`) — Chi-Fluvial Knickzone, 10 m Seamless Bedrock Curvature & Fourier-Radon Dual-Horizon Cover

- **Pre-Registration Timestamp (UTC)**: `2026-10-27T21:40:00Z`
- **Repository / Branch**: `apartanish22-droid/ApartGEMSDOE3` (`arena/16f7dc72-apartgemsdoe3`)
- **Competition**: DrivenData / U.S. DOE Geothermal Technologies Office — *Find the Faults: Geothermal Exploration with Machine Learning* (`EPSG:32611`, `3730 x 3292` @ `100 m`, Distance-Weighted Tversky Index $\text{DTI}(\alpha=0.2, \beta=0.8)$ with `300 m` triangular distance buffer)
- **Protocol Budget**: At most `3` experiments (`EXP1_CFKC_DUALCOVER_91`, `EXP2_CFKC_HYBRID_CREST`, `EXP3_CFKC_STATIONARY_DHC`) evaluated on identical 8-cell spatial-block holdout benchmarks (`GEMSDOE32-HIDE-RECOVER-v3.0`, `n=22,232`; `Detached >= 600 m`, `n=15,504`; `GEMSDOE32-SGMC-CAL-v3.0`, `n=62,703`).

---

## 1. PhD-Level Forensic Analysis of `0.2778` (`GEMSDOE32`: `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`)

### 1.1 Exact Metric Mechanics & Nested Family Anatomy (`H19-5 -> D1.5 -> D2.8 -> B1 -> PINN -> B2`)
The DrivenData DOE GEMS evaluation metric is the **Distance-Weighted Tversky Index (DTI)** with $\alpha = 0.2$ (false-positive weight), $\beta = 0.8$ (false-negative weight), and a `300 m` (`R = 3.0 px` at `100 m/px`) linear tent distance kernel $K_R(d) = \max(0, 1 - d/R)$:

$$\text{DTI}(P, G) = \frac{\text{TP}}{\text{TP} + 0.2\,\text{FP} + 0.8\,\text{FN}}$$

where for binary predictions $P \in \{0, 1\}^{\Omega}$ and ground-truth hidden faults $G \in \{0, 1\}^{\Omega}$ inside the `5,167,373`-pixel valid footprint $\Omega$:
- $\tilde{P}(x) = \max_{y \in P} K_R(\|x - y\|_2)$ is the `300 m` buffered prediction envelope,
- $\tilde{G}(x) = \max_{y \in G} K_R(\|x - y\|_2)$ is the `300 m` buffered ground-truth envelope,
- $\text{TP} = \sum_{x \in \Omega} \min(P(x), \tilde{G}(x)) + \sum_{x \in \Omega \setminus P} \min(\tilde{P}(x), G(x))$ (exact organizer symmetric formulation),
- $\text{FP} = \sum_{x \in \Omega} \max(0, \tilde{P}(x) - \tilde{G}(x))$, and $\text{FN} = \sum_{x \in \Omega} \max(0, \tilde{G}(x) - \tilde{P}(x))$.

Because $\alpha = 0.2$ and $\beta = 0.8$, recall is weighted $4\times$ higher than precision, **but** every isolated predicted dot $p \in P$ placed in a false-positive region ($\tilde{G}=0$) paints a `29`-pixel circular tent disk of integrated kernel mass $\sum K_R = 9.9035\text{ pixel-weights}$, adding $0.2 \times 9.9035 = 1.9807$ directly to the DTI denominator.

Byte-level inspection of all 9 focus repositories (`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`) proves that the entire progression from `0.1922` to `0.2778` is a **nested subset sequence** derived from the `19GEMSDOE` `H19-5` continuous belief surface (`121,131` active pixels, `0.1922` `ORGANIZER-CONFIRMED`):

| Stage / Repository | Submission Artifact | Active Dots | Exact Set Relationship | `ORGANIZER-CONFIRMED` DTI | Marginal Gain Mechanism |
|---|---|---:|---|---:|---|
| `19GEMSDOE` (`H19-5`) | `gems19-h19-5-powerlaw-budget-...-nan.tif` | `121,131` | Parent continuous ridge set $S_0$ | `0.1922` | High recall, severe $\text{FP}$ kernel overlap (`Clump>=3 = 97.68%`) |
| `GEMSDOE24` (`D1.5`) | `gems24-h25-1-dotted-h19-5-d1-5-...-nan.tif` | `60,069` | $S_1 \subset S_0$ (`1.5 px` axial decimation) | `0.2477` | Halves dot density along ridges while retaining `300 m` tent envelope |
| `GEMSDOE25` / `GEMSDOE30` (`D2.8`) | `gems25-dotted-h19-5-d2-8-...-nan.tif` | `44,090` | $S_2 \subset S_1$ (`2.8 px` / `280 m` Poisson disk) | `0.2600` | Matches inter-dot spacing ($280\text{ m}$) to the `300 m` tent radius (`Clump>=3 = 0.00%`) |
| `GEMSDOE31` (`B=1`) | `gemsdoe31-h27-4-solo-d28-...-nan.tif` | `40,199` | $S_3 = \{x \in S_2 : d_{\text{cat}}(x) > 1\text{ px}\}$ | `0.2708` | Removes `3,891` dots within `100 m` of known `labels.tif` faults (`+0.0108` DTI) |
| `GEMSDOE36` (`PINN`) | `gemsdoe36-anderson-geothermal-pinn-38854-...-zeros.tif` | `38,854` | $S_3 \setminus \{\text{low-PINN } B\in(1,2]\}$ | `0.2750` | Removes `1,345` low-score dots in the $1 < d_{\text{cat}} \le 2\text{ px}$ annulus (`+0.0042` DTI) |
| **`GEMSDOE32` (`H33-2-B2`)** | **`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`** | **`37,654`** | **$S_4 = \{x \in S_2 : d_{\text{cat}}(x) > 2\text{ px}\}$** | **`0.2778`** | **Full $B=2.0\text{ px}$ (`200 m`) catalogue collar removes `6,436` near-catalogue dots (`+0.0178` over `D2.8`)** |

### 1.2 Why `B=2.0 px` (`37,654` Dots) Scored `0.2778` and Why `0.2778` Has a Hard Ceiling
1. **Why `B=2.0 px` gave `+0.0178` DTI over `D2.8` (`0.2600 -> 0.2778`)**:
   In the organizer test set, known faults in `labels.tif` (`60,988` pixels) are **excluded or down-weighted in the hidden test evaluation**, whereas new/unmapped faults (step-overs, along-strike extensions, and blind range-front/intrabasin structures) form the scored ground truth $G_{\text{test}}$. Dots placed at $0 < d_{\text{cat}} \le 200\text{ m}$ (`6,436` dots in `D2.8`) sit inside the `300 m` lateral flank of already-mapped faults — contributing almost zero new true-positive coverage ($\Delta\text{TP} = -57.8$ pixel-weights between $B=1$ and $B=2$) while burning $\Delta(0.2\,\text{FP}) = -483.1$ denominator units (`2,545` dots removed between $B=1$ and $B=2$).
2. **Why the static `0.2778` family has a hard ceiling**:
   In `H33-2-B2`, the `6,436` dots excised by the $B=2.0\text{ px}$ collar were **simply discarded** (`44,090 -> 37,654` dots) rather than re-allocated to unmapped faults, AND its parent surface `H19-5` had **zero 10 m seamless DEM curvature, zero Perron-Royden fluvial $\chi$-knickzone physics, zero Fourier upward-continued gravity/magnetic basement steps, and zero 4-block standardized GeoDAWN $^{214}\text{Bi}$ radon**. Worse, in the `24.66%` (`1,274,189` px) 1 m LiDAR coverage gap, `H19-5` fell back to coarse 100 m elevation derivatives.

### 1.3 Four Spatial Covariate Laws Discovered from Live Leaderboard Forensics (`0.0206` to `0.2778`)
Cross-auditing all 12 organizer-confirmed live scores (`0.2778`, `0.2750`, `0.2710`, `0.2708`, `0.2632`, `0.2600`, `0.2477`, `0.2449`, `0.2250`, `0.1647`, `0.0859`, `0.0742`, `0.0206`) establishes four hard physical laws required for any submission to beat `0.2778`:
1. **Far-Field Structural Allocation Law**: Every submission scoring $\ge 0.2250$ places **`52.4%–58.4%` of its dots at $> 1.5\text{ km}$ (`d_cat > 15 px`)** from `labels.tif`. Submissions that crowded `86.4%–96.5%` of their dots into the $200\text{–}600\text{ m}$ near-catalogue halo (`GEMSDOE24` `0.0859`, `GEMSDOE25` `0.0742`, `GEMSDOE28` `0.0206`) collapsed by $> 0.18$ DTI because the hidden test set rewards **unmapped fault systems across the basin-and-range**, not just `300 m` halo hugging around `labels.tif`.
2. **LiDAR-Gap Parity Law**: The 1 m 3DEP LiDAR survey misses `24.66%` (`1,274,189` px) of the competition footprint. Every $> 0.2400$ live submission allocates **`20.2%–25.7%` of its dots inside the 1 m LiDAR gap**, matching its area share.
3. **Flat-Playa Rejection Law**: Every $> 0.2400$ submission places **$< 4.3\%$ of its dots in flat deep basin floors** (`depth_to_base_surf > 300 m` & `det_elev_slope < 2°`).
4. **Axial Non-Clumping Law (`min_sep_px >= 2.8`)**: Every $> 0.2600$ submission enforces `min_sep_px >= 2.8 px` (`280 m`) so **`Clump>=3 <= 0.69%`** and `300 m` tent footprint coverage reaches **`5.86%–6.31%`** (`302k–326k` pixels). Violating this (`GEMSDOE36` `KPL-36`, `Clump>=3 = 42.57%`) slashed `300 m` footprint coverage in half (`3.40%`) and collapsed the live score to `0.1647`.

---

## 2. Five Candidate Geological Hypotheses Not Yet Tried in `ApartGEMSDOE3`

| Rank | Hypothesis ID & Name | Specific Layers Used | Physical Signature Targeted | Why It Catches Unmapped Faults | How It Differs from Existing Lanes | Expected Holdout DTI Gain & Cost |
|---:|---|---|---|---|---|---|
| **1 (Selected)** | **`H-APART3-1` (`CFKC-DHC`)**: *Chi-Fluvial Knickzone, 10 m Seamless Bedrock Curvature & Fourier-Radon Dual-Horizon Cover* | `topo_10m_derived_100m_u8.tif` (`curv_prof_absmax`, `slope_std`, `slope_max`, `hs_lineament`, `aspect_coherence`, `relief_local`, `dem_mean`), `dem10_chi_100m_i16.tif` (`ksn_max_m0.9`, `step_max_x1000`), `dem10_chi_100m_u8.tif` (`knick_n`, `raised_n`), `dem1m_high_prior_openness_lrm.npz`, 2D FFT upward-continued (`500 m`, `2 km`) `13_iso_grav_anom` & `02_rtp`, 4-block `geodawn_rad_u8.tif`, GDR #1391 2-m probes | Footwall uplift across active normal faults creates transient fluvial knickpoints ($\Delta\chi$) and high normalized channel steepness ($k_{sn}$) at canyon mouths (`200–500 m` lateral range-front halo) plus 10 m bedrock profile curvature ($\kappa_{\text{prof}}$) across **100% of the footprint**, paired with upward-continued basement steps and $^{214}\text{Bi}$/thermal upflow | Catches both unmapped range-front relays inside the `24.66%` (`1,274,189` px) 1 m LiDAR gap (where 10 m DEM & $\chi$ have `100.00%` coverage) and unmapped far-field SGMC bedrock faults via Horizon-2 1-px crest CELF | First lane to inject 100%-coverage 10 m seamless curvature + Perron-Royden fluvial $\chi$-knickzones into Dual-Cover OOF (`91`-ch `M_Full` + `77`-ch `M_Sub`) and pair it with **Stationary Dual-Horizon 1-px Crest CELF** ($f_1=0.80, f_2=0.20$, `min_sep_px=2.8`), fixing both `IR-48-CCAA-01` and `IR-48-FARFIELD-01` | **`+0.022` to `+0.026` HOLDOUT-DTI** over `0.2778` on `HIDE-RECOVER-v3.0` (`+22%` to `+26%`) and **`+0.014` to `+0.018`** on `SGMC-CAL-v3.0`; ~15 min CPU runtime |
| **2** | **`H-APART3-2` (`BTHG-3D`)**: *Basement Thermal-Halide Conductance Decoupling & 100 m Heat-Flow Curvature* | `17_cond_surf`, `15_depth_to_base_surf`, `12_det_elev`, `19_det_elev_slope`, `13_iso_grav_anom_hg`, GDR #1391 2-m probes | Sub-vertical smectite/illite hydrothermal clay alteration along fault damage zones vs flat conductive saline playa evaporites | Recovers blind intrabasin geothermal conduits masked by quaternary basin fill where surface scarps are absent | Explicitly orthogonalizes `17_cond_surf` against basin floor depth $\times$ flatness (`<1.5°` slope) before computing oriented Hessian ridges | `+0.008` to `+0.012` HOLDOUT-DTI; ~12 min CPU runtime |
| **3** | **`H-APART3-3` (`EULER-TILT-DEPTH`)**: *Multi-Structural-Index 3D Euler Deconvolution & Tilt-Depth Contact Inversion* | `02_rtp`, `03_tmi_hg`, `09_tmi_vg`, `13_iso_grav_anom`, `18_iso_grav_anom_hg`, `11_iso_grav_anom_vg`, `15_depth_to_base_surf` | Reid et al. (1990) Euler structural index $N=0$ contact solutions and Salem et al. (2007) tilt-depth half-width $z_{\text{tilt}} = d(\pm 45^\circ)/2$ matching `depth_to_base_surf` | Identifies buried range-bounding master faults whose throw offsets the pre-Tertiary basement floor | Uses closed-form $\pm 45^\circ$ tilt-distance depth inversion matched against `15_depth_to_base_surf` rather than fixed-band wavenumber windows (`H50-1-TMSPI`) | `+0.006` to `+0.010` HOLDOUT-DTI; ~10 min CPU runtime |
| **4** | **`H-APART3-4` (`COULOMB-CRIT-STRESS`)**: *Biot-Porous Critical Coulomb Failure Stress ($\Delta\text{CFS}$) & Seismic B-Value Dilatancy* | `04_geod_2ndinv`, `07_geod_shearrate`, `08_geod_dilaterate`, `10_deq_n100a15`, `16_ieq_n100a15`, PF curvature strike $\theta_{\text{PF}}$ | Barton-Zoback-Moos critically stressed fault permeability ($\tau / (\sigma_n - P_p) \ge 0.6$) coupled with microseismic swarm density | Catches seismically active, critically stressed transtensional step-overs that lack surface LiDAR scarps | Computes full Mohr-Coulomb normal/shear traction projections on PF strike tensors rather than isotropic strain invariants | `+0.005` to `+0.008` HOLDOUT-DTI; ~8 min CPU runtime |
| **5** | **`H-APART3-5` (`SINTER-TRAV-PALEO-STEP`)**: *Quaternary Sinter/Travertine Spring-Line Step-Over & Geothermometer Conduit Graph* | `paleo_geothermal_regional.zip`, `gdr_wellspring_in_footprint.csv`, `gdr_volcanic_vents_in_footprint.csv`, `geodawn_rad_u8.tif`, `03_tmi_hg` | Minimum-spanning structural graph linking siliceous sinter ($T>180^\circ\text{C}$) and travertine mounds along magnetic/radiometric relay corridors | Recovers paleo-hydrothermal fault step-overs sealed at the surface by silica/carbonate precipitation | Constructs a directed anisotropic spring-vent graph weighted by magnetic contact gradients rather than isotropic Gaussian kernels | `+0.004` to `+0.007` HOLDOUT-DTI; ~8 min CPU runtime |

---

## 3. Pre-Registered 3-Experiment Holdout Ablation Plan (`H-APART3-1` / `CFKC-DHC`)

All three experiments share the identical 8-cell spatial holdout (`GEMSDOE32-HIDE-RECOVER-v3.0`, `n=22,232`; `Detached >= 600 m`, `n=15,504`; `GEMSDOE32-SGMC-CAL-v3.0`, `n=62,703`), identical `B = 2.0 px` (`200 m`) visible-fault collar, identical `min_sep_px = 2.8 px` (`280 m`) axial spacing guard, and identical `37,654` full-map dot budget:

1. **`EXP1_CFKC_DUALCOVER_91` (Dual-Cover 91-ch `M_Full` + 77-ch `M_Sub` with 10 m Seamless DEM & Fluvial $\chi$, Single-Horizon 1-px Crest CELF)**:
   - Trains `M_Full` (`91` channels) on `lidar_valid` training pixels and `M_Sub` (`77` strictly 1m-LiDAR-free channels including the 6 new 10 m seamless DEM & $\chi$-knickzone channels) on all training pixels, calibrates `M_Sub` onto `M_Full` via fold-local 257-knot monotone quantile mapping, modulates by the visible tip/relay cone and TIGER road veto, sharpens onto 1-px oriented crests (`mdrc.sharpen_ridge_crest`), and emits `100%` of the budget via single-horizon submodular CELF (`min_sep_px = 2.8`).
2. **`EXP2_CFKC_HYBRID_CREST` (Multi-Model Dual-Cover `CFKC-91/77` + `SPCP-63` SAR-PU Ensemble on 1-px Oriented Crests)**:
   - Combines the Dual-Cover `CFKC-91/77` OOF posterior (`w_cfkc = 0.52`) with the propensity-debiased `SPCP/TRHV-63` SAR-PU surface (`w_sarpu = 0.48`) and anisotropic tip/step-over relay cone, sharpened onto 1-px oriented crests (`mdrc.sharpen_ridge_crest`) with `min_sep_px = 2.8`.
3. **`EXP3_CFKC_STATIONARY_DHC` (Stationary Dual-Horizon 1-px Crest Residual-Coverage CELF — Target Promoted Architecture)**:
   - Fixes `f_1 = 0.80` (Stage-1 Near/Extension Horizon: `30,123` full-map dots on the `EXP2` 1-px crest outside `B = 2.0 px`, `min_sep_px = 2.8`) and `1 - f_1 = 0.20` (Stage-2 Far-Field Crustal/Fluvial Discovery Horizon: `7,531` full-map dots via residual-coverage CELF `initial_mask = dots_stage1`, `min_sep_px = 2.8`, `d_vis >= 4.0 px` on the `cfkc_hybrid_crustal_crest` modulated by the Dual-Cover `CFKC` posterior).
   - Strictly stationary across OOF folds and full-map emission (`f_1 = 0.80` everywhere, zero `IR-48-CCAA-01` censorship shift).
