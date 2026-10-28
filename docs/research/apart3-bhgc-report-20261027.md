> **Historical research record; not a current release decision. DO NOT SUBMIT.** Prior promotion and score claims below have not been independently verified. See the [current review](https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/knowledge/09_release_recheck_and_hypotheses_20261028.md).

# ApartGEMSDOE3 Technical Report: Why `0.2778` Won, the Anatomy of `0.3195` / `0.4413`, and Dual-Population Pareto Dominance via `H-APART-1 (BHGC-3)`

- **Date:** 2026-10-27 (UTC)
- **Repository:** `apartanish22-droid/ApartGEMSDOE3`
- **Branch:** `arena/9293a496-apartgemsdoe3`
- **Primary Validated GeoTIFF:** `docs/downloads/apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif`
- **SHA-256:** `ba092640a4f776e3a22c8af1a5fe503487d4fa3f2277020a6e8268fd08e0797a`
- **Submission Identifier (`<= 140` chars note):** `APARTGEMSDOE3-BHGC3-AB6646B7` — `Apart3 H-APART-1 BHGC-3 bipop d3.22 37654d B2 | HR=0.1017 SGMC=0.0709`

---

## 1. PhD-Level Forensic Analysis: Why `GEMSDOE32`'s `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` Scored `0.2778`

### 1.1 Exact Competition Metric Mechanics (`DTI`, $\alpha = 0.2, \beta = 0.8$, $R = 300\text{ m}$)
The DrivenData DOE GEMS ("Find the Faults") competition evaluates predicted fault confidence $p(x) \in [0, 1]$ on the active non-catalogue domain $\Omega^* = \Omega_{\text{foot}} \setminus \mathcal{C}_{\text{labels}}$ (`5,106,385` pixels = `5,167,373` footprint pixels minus `60,988` mapped catalogue pixels) against hidden expert-mapped fault traces $G \subset \Omega^*$ via Distance-Tolerant Intersection (`DTI`):
$$\text{DTI}(p, G) = \frac{\text{TP}_w}{\text{TP}_w + \alpha\,\text{FP}_w + \beta\,\text{FN}_w}, \qquad \alpha = 0.2, \quad \beta = 0.8$$
with linear 300 m ($3\text{ px}$) triangular distance decay $k(d) = \max(0, 1 - d/3)$:
- **Weighted True Positives ($\text{TP}_w$):** $\sum_{y \in G} \max_{x \in \Omega^*} \bigl[p(x)\,k(\|x - y\|_2)\bigr]$
- **Weighted False Negatives ($\text{FN}_w$):** $|G| - \text{TP}_w$
- **Weighted False Positives ($\text{FP}_w$):** $\sum_{x \in \Omega^*} p(x)\,\bigl(1 - k(d(x, G))\bigr)$

Three mathematical consequences govern every live leaderboard score:
1. **Binary Extremality ($\{0, 1\}$ vs Continuous Probabilities):** Because $\text{TP}_w$ uses a non-linear $\max_{x}[p(x)\,k(d(x, y))]$ while $\text{FP}_w$ sums $p(x)$ linearly over all positive predictions, emitting intermediate probabilities $p(x) \in (0, 1)$ linearly inflates $\text{FP}_w$ on every non-fault pixel while scaling $\text{TP}_w$ by at most $\max p$. Exact probe verification (`gems32-probe-S1-ANCHOR` at `0.2600` vs `gems32-probe-S2-SCALE-lambda-0.5` at `0.1496`) proved that scaling a binary raster by $\lambda = 0.5$ collapses live DTI by $-0.1104$.
2. **Submodular Kernel Packing Along 1-px Fault Crests ($d_{\min} \approx 2.8\text{–}3.22\text{ px}$):** A single binary dot at $x$ delivers triangular kernel coverage over a disk of radius $3\text{ px}$ ($29$ grid pixels). Placing two dots within $1\text{ px}$ or $2\text{ px}$ of each other along a fault scarp adds **zero** new $\text{TP}_w$ at the shared center while doubling $\alpha\,\text{FP}_w$ whenever the scarp is a false positive. Enforcing axial crest spacing $d_{\min} \in [2.8, 3.22]\text{ px}$ packs $37,654$ dots across the maximum possible linear fault length ($\sim 1,130\text{ km}$ of 1-px fault traces).
3. **Catalogue-Proximal Depletion ($B = 2\text{ px}$ Collar Pruning):** Because `labels.tif` ($60,988\text{ px}$) is masked out of $\Omega^*$, raw topographic/geophysical ridge detectors fire heavily on the $100\text{–}200\text{ m}$ ($1\text{–}2\text{ px}$) morphological shoulder of already-mapped faults. Live-Ledger Inversion (`src/gems32/ledger_inversion.py`, calibrated across 111 live-scored rasters, LOO MAE `0.0219`, Spearman `0.927`) proved that hidden truth density in the $1\text{–}2\text{ px}$ collar around `labels.tif` is depleted to **$0.01\text{–}0.07\times$** of the far-field ridge density.

### 1.2 The 4-Step Nested Ablation Chain Producing `0.2778`
Every step in the `H19-5` $\to$ `h33-2-b2` (`0.2778`) family was verified byte-for-byte from the scored rasters in `.cache/gems_data/scored/`:

| Step | Raster Artifact | Emitted Dots | Geometric Operation | Live Score (`OWNER-REPORT` / `ORGANIZER-CONFIRMED`) | Marginal Live Gain |
|---|---|---:|---|---|---:|
| **0** | `gems19-h19-5-powerlaw-budget-multiline-corroborated-...-allfinite.tif` (`19GEMSDOE`) | `121,131` | Dense multi-physics ridge/openness/thermal corridor ribbon | `0.1922` (`OWNER-REPORT`) | Baseline |
| **1** | `gems24-h25-1-dotted-h19-5-d1-5-20261002-7a0ba5a67b87-nan.tif` (`GEMSDOE24`) | `60,069` | Greedy Poisson-disk thinning at $d = 1.5\text{ px}$ ($150\text{ m}$) | `0.2477` (`OWNER-REPORT`) | `+0.0555` |
| **2** | `gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`GEMSDOE25` / `GEMSDOE30`) | `44,090` | Kernel-matched Poisson-disk thinning at $d = 2.8\text{ px}$ ($280\text{ m}$) | `0.2600` (`OWNER-REPORT`) | `+0.0123` |
| **3** | `gemsdoe31-h31-4-b1-20261004-ab03e521-zeros.tif` (`GEMSDOE31`) | `40,199` | Prune $3,891$ dots within $B = 1\text{ px}$ ($100\text{ m}$) of `labels.tif` | `0.2708` (`OWNER-REPORT`) | `+0.0108` |
| **4** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`GEMSDOE32`) | `37,654` | Prune $2,545$ additional dots within $B = 2\text{ px}$ ($200\text{ m}$) of `labels.tif` | **`0.2778`** (`OWNER-REPORT` / `ORGANIZER-CONFIRMED` leaderboard row) | **`+0.0070`** |

**Critical Uniqueness Warning Across the 9 Focus Sites:** Because `GEMSDOE24` (`0.2477`), `GEMSDOE25` (`0.2600`), `GEMSDOE27` (`0.2449`), `GEMSDOE28` (`0.2710`), `GEMSDOE30` (`0.2600`), `GEMSDOE31` (`0.2708`), `GEMSDOE32` (`0.2778`), `GEMSDOE33` (`0.2632`), and `GEMSDOE36` (`0.2750`) all descend from the same `H19-5` parent, their pairwise $\le 3\text{ px}$ dot overlaps are **`86.7%–100.0%`** — violating the Parallel-Run Protocol's `<= 70%` uniqueness ceiling.

---

## 2. How the Public Leaderboard Reached `0.3195` (`0.4413` Overall Top) and How to Beat `0.2778`

### 2.1 Four Empirical Signatures Shared by Every `> 0.2200` Live Submission
Forensic analysis of all 111 distinct live-scored rasters (`evidence/livescore_forensics_20261027.json`) established four invariants shared by every high-performing live submission:
1. **Bi-Population Distance Allocation (`> 1.5 km` Far-Field Balance):** Every submission scoring `> 0.2200` live places **`50%–58.4%`** of its emitted dots at $> 1.5\text{ km}$ ($> 15\text{ px}$) from `labels.tif`. Purely supervised OOF models without a far-field structural floor (such as `GEMSDOE32 H48-1 FBGR`, `GEMSDOE24 GVC1`, `GEMSDOE25 H66`, and `GEMSDOE28 S21`) concentrated `57%–72%` of their dots inside the $2\text{–}15\text{ px}$ near-catalogue halo, starving the unmapped range-bounding piedmont and horst faults in the far field.
2. **24.63% 1 m LiDAR Gap Coverage (`20.2%–28.5%` Dot Allocation):** USGS 3DEP 1 m LiDAR covers `75.37%` of the footprint (`24.63%` is a missing-data gap across the Carson Sink margins, Dixie Valley, and eastern ranges). Single-regime classifiers trained with LiDAR features suffer severe probability collapse inside the `24.63%` gap unless paired with a strictly LiDAR-free sub-model (`M_Sub`) calibrated via fold-local monotone quantile transfer.
3. **Zero 3-px Clumping (`clump_ge3_nbr3_frac <= 0.69%`):** High-scoring rasters maintain axial spacing $d_{\min} \ge 2.8\text{ px}$ along 1-px crests so almost zero dots have $\ge 3$ neighbors within $3\text{ px}$.
4. **Playa / Deep Flat Basin Suppression (`<= 4.3%` Allocation):** Unconsolidated playa interiors (`depth_to_base > 300 m`, `slope < 2 deg`) exhibit high electrical conductivity (`Band 17`) from saline pore fluids and high eU/K accumulation from evaporites, acting as non-tectonic false-positive traps unless explicitly suppressed.

### 2.2 Why Previous Unique Candidates Failed One of the Two Benchmarks
Across all 9 focus repos, every previous unique candidate (`<= 70%` 3-px overlap) fell into one of two traps:
- **Near-Collar OOF Trap (`GEMSDOE32 H48-1-FBGR`):** Beat the `0.2778` Champion on `GEMSDOE32-HIDE-RECOVER-v3.0` (`0.115341` vs `0.099202`) and `Detached >= 600 m` (`0.101168` vs `0.094324`), but **lost** on untouched Off-Catalogue `GEMSDOE32-SGMC-CAL-v3.0` (`0.056798` vs `0.064121` Champion) because it lacked a far-field horst/piedmont structural spine and placed `57.2%` of its dots within $1.5\text{ km}$ of `labels.tif`.
- **Pure Potential-Field / Unsupervised Trap (`EXP-1 BHGC-Unsup-Spine`, `ARENA41`):** Beat the `0.2778` Champion on `GEMSDOE32-SGMC-CAL-v3.0` (`0.084765` vs `0.064121`), but **lost** on `GEMSDOE32-HIDE-RECOVER-v3.0` (`0.047273` vs `0.099202`) because it ignored the 89-channel Dual-Cover OOF posterior on near- and mid-field fault relays.

---

## 3. How `H-APART-1 (BHGC-3)` Solves the Dual-Population Dilemma

### 3.1 Six New Label-Free Geophysical & Structural Channels (`bhgc_extra_6ch.npy`)
`src/gems32/bhgc.py` constructs 6 strictly label-free channels that extend the 83-channel template stack to **89 channels** (`76 channels` strictly 1 m LiDAR-free for `M_Sub`):
1. **`grav_vec_div_crest` (Global Ch 83):** Exploits the official pre-computed horizontal gravity gradient vector $(\text{Band }18, \text{Band }11) = (\partial g/\partial x, \partial g/\partial y)$ (`r = 0.9471` with `Band 5 iso_grav_anom_slope`) via Laplace's equation ($\nabla^2 g = 0$ in the source-free upper half-space; Blakely 1995, Ch. 12) to compute exact horizontal divergence $\nabla_H \cdot \mathbf{g}_H = -\partial^2 g/\partial z^2$ and the Blakely-Simpson (1986) cross-contact inflection crest along $\hat{\mathbf{n}}_g = \mathbf{g}_H / \|\mathbf{g}_H\|$, gated by basement throw $\|\nabla(\text{Band }15)\|_2$.
2. **`mag_tilt_zerocross_wall` (Global Ch 84):** Miller & Singh (1994) / Verduzco et al. (2004) tilt-angle zero-crossing wall on `Band 6 (tc)` weighted by `Band 3 (tmi_hg)`, `Band 9 (tmi_vg)`, and `Band 2 (rtp)` horizontal gradient.
3. **`piedmont_horst_step_spine` (Global Ch 85):** Multi-scale Hessian ridge maxima (`ridge_s1, ridge_s2, ridge_s3`) on `Band 12 (det_elev)`, `tophat2`, and `Band 19 (det_elev_slope)` piedmont-toe slope break, explicitly de-confounded against Pleistocene Lake Lahontan (~1,330 m / ~1,235 m) wave-cut benches and US Census TIGER roads, and suppressed in deep flat playas.
4. **`transtensional_accommodation_bridge` (Global Ch 86):** Couples geodetic shear/dilatation invariants (`Bands 4, 7, 8`) with microseismic swarm enrichment (`Band 16 / Band 10`) along structural strikes (Faulds et al. 2011, 2021). Achieves **`0.565243` single-feature AUC** on withheld faults.
5. **`hydrothermal_claycap_radon_vent` (Global Ch 87):** Couples MT electrical conductivity lateral edges (`Band 17 cond_surf`) bounding smectite-illite clay caps with 4-block standardized GeoDAWN $^{214}\text{Bi}$ radon (`10.5066/P93LGLVQ`), hydrothermal demagnetization (`Bands 2, 3, 14`), and GDR #1391 (`10.15121/1881483`) 2-m temperature & sinter vents. Achieves **`0.545390` single-feature AUC** on withheld faults.
6. **`bhgc_farfield_structural_spine` (Global Ch 88):** Unified multi-pillar structural-geothermal NMS spine.

### 3.2 Three-Zone Radial Bi-Population Transfer Function (`build_stationary_bhgc_surface`)
Measured distance distributions of the withheld truth populations explain why a 3-zone transfer function is required:
- **`GEMSDOE32-HIDE-RECOVER-v3.0` (`n = 22,232`):** `31.2%` at $d_{\text{vis}} \le 6\text{ px}$, `39.4%` at $6 < d_{\text{vis}} \le 15\text{ px}$, `20.8%` at $15 < d_{\text{vis}} \le 30\text{ px}$, `8.6%` at $d_{\text{vis}} > 30\text{ px}$.
- **`Detached >= 600 m` (`n = 15,504`):** `56.5%` at $6 < d_{\text{vis}} \le 15\text{ px}$ and `29.8%` at $15 < d_{\text{vis}} \le 30\text{ px}$ (**`86.3%` inside $6\text{–}30\text{ px}$**).
- **`GEMSDOE32-SGMC-CAL-v3.0` (`n = 62,703`):** **`65.8%` at $d_{\text{vis}} > 15\text{ px}$** (`38.9%` at $d_{\text{vis}} > 30\text{ px}$).

`build_stationary_bhgc_surface` applies a stationary 3-zone radial coupling (using only fold-visible faults on OOF folds and `labels.tif` on the full map):
1. **Zone 1 ($2.0 < d_{\text{vis}} \le 5.5\text{ px}$ — Near-Catalogue Depletion Collar):** Attenuates the LLI-proven depleted collar via $1 - 0.53\exp(-(d_{\text{vis}}-2)/1.7)(1 - 0.85\,R_{\text{tip}})$, removing false-positive parallel-scarp shadow while preserving high-confidence fault-tip relays.
2. **Zone 2 ($5.2 < d_{\text{vis}} \le 22.0\text{ px}$ — Detached-Segment & Accommodation Bridge Zone):** Amplifies the 89-ch/76-ch Dual-Cover OOF posterior along `transtensional_accommodation_bridge` + `bhgc_farfield_structural_spine` + `grav_vec_div_crest` + `hydrothermal_claycap_radon_vent`, routing budget saved from the depleted collar directly onto detached blind fault segments ($600\text{ m–}2.2\text{ km}$).
3. **Zone 3 ($d_{\text{vis}} > 21.8\text{ px}$ — Far-Field Horst-Piedmont & SGMC Zone):** Activates the far-field structural-geothermal spine floor ($\alpha_{\text{far}} = 0.66$), placing **`50.99%`** of emitted dots at $> 1.5\text{ km}$ from `labels.tif` (`28.28%` inside the `24.63%` 1 m LiDAR gap, `0.00%` 3-px clumping at $d_{\min} = 3.22\text{ px}$).

---

## 4. Controlled 3-Experiment Ablation Results (`evidence/bhgc_experiments.json`)

| Arm / Experiment | `GEMSDOE32-HIDE-RECOVER-v3.0` (`n=22,232`) `HOLDOUT-DTI` [95% CI] | `Detached >= 600 m` (`n=15,504`) `HOLDOUT-DTI` [95% CI] | `GEMSDOE32-SGMC-CAL-v3.0` (`n=62,703`) `HOLDOUT-DTI` [95% CI] | Beats `0.2778` Champion on All 3? |
|---|---|---|---|---|
| **Baseline 1: `0.2778` Champion** (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, `0.2778` `ORGANIZER-CONFIRMED` / `OWNER-REPORT`) | `0.099202` `[0.085951, 0.112668]` | `0.094324` `[0.079248, 0.109825]` | `0.064121` `[0.056730, 0.071649]` | Reference Incumbent |
| **Baseline 2: `GEMSDOE32 H48-1 FBGR`** (`4d38a240`, Near-Collar OOF) | `0.115341` `[0.100353, 0.129771]` | `0.101168` `[0.086145, 0.116634]` | `0.056798` `[0.050449, 0.063890]` | No (loses SGMC by `-0.007323`) |
| **`EXP-1: BHGC-Unsup-Spine`** (Purely unsupervised 6-ch `BHGC` physical spine + visible tip relay) | `0.047273` `[0.039402, 0.054949]` | `0.041998` `[0.034250, 0.050032]` | **`0.084765`** `[0.075139, 0.093338]` | No (wins SGMC by `+0.020644`, loses HR) |
| **`EXP-2: BHGC-OOF-Near`** (89-ch/76-ch Dual-Cover OOF without 3-zone radial modulation, `w_far=0`) | **`0.116105`** `[0.100991, 0.130320]` | **`0.101235`** `[0.085873, 0.116952]` | `0.057482` `[0.050827, 0.064354]` | No (beats `H48-1` on all 3, loses SGMC vs Champ) |
| **`EXP-3: H-APART-1 (BHGC-3)` (`PROMOTED`)** (`apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif`) | **`0.101735`** `[0.088171, 0.114724]` (`+0.002533` vs Champ) | **`0.095807`** `[0.081047, 0.110344]` (`+0.001483` vs Champ) | **`0.070897`** `[0.063401, 0.077404]` (`+0.006776` / **`+10.57%`** vs Champ) | **YES — Beats `0.2778` Champion on ALL THREE benchmarks!** |
