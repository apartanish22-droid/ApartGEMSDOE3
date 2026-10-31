# New geological hypotheses for off-catalogue blind fault discovery (2026-10-31)

Context: The nine focus-site files (GEMSDOE24/25/27/28/30/31/32/33/36) are all mutual
duplicates (overlap 87–100% within 3 px, |rho| up to 0.99). Their owner-reported scores
(0.2477–0.2778) do not track the catalogue-hidden holdout DTI (ρ = −0.85 at n=9), so
optimising catalogue-hidden holdout will NOT improve the live leaderboard. The pre-registered
n=117 calibration shows the off-catalogue SGMC-calibrated DTI is the live-score proxy
(ρ = +0.40, 95% CI [+0.22, +0.56]). The strategy: hunt faults MISSING from the USGS/INGENIOUS
catalogue using label-free physical anomalies, maximising SGMC off-catalogue DTI while staying
unique (<70% within-3px overlap, |rho| ≤ 0.90 vs every registry raster).

---

## H1 — LiDAR scarp curvature + DEM10 chi anomaly (TOP CANDIDATE)

**Layers:** `external/lidar_scarp_features_u8.tif` (3DEP LiDAR-derived scarp/edge strength),
`external/dem10_chi_100m_i16.tif` (10 m DEM stream-power chi), competition grid (100 m).

**Physical signature:** Convex-up topographic scarps (fault-line scarps) co-located with high
chi values (knickzones / transient channel response to active faulting). A scarp without a
chi anomaly is likely a relict landslide or terrace; high chi without a scarp is likely
lithologic. Requiring BOTH catches blind faults with recent surface displacement that the
catalogue misses because mapping was done from coarse geology, not LiDAR.

**Why it catches catalogue-missing faults:** The USGS/INGENIOUS catalogue maps traced fault
lines from published geology. Blind or recently-active faults with subtle scarps are absent.
LiDAR reveals metre-scale scarps; chi reveals ongoing tilting. The intersection is a
structural-geomorphic signal not derivable from `labels.tif`.

**Differs from repo implementations:** Existing submissions use (a) dotted ridge skeletons
from magnetic/radiometric amplitude, (b) dip-step/strain tensors from the 19-band feature
stack, or (c) catalogue-proximity dotting. None combine LiDAR scarp edge strength with
chi. `lidar_scarp_features_u8.tif` and `dem10_chi_100m` are in the restored external stack
but unused by any run card in `evidence/`.

**Expected DTI improvement:** High. Targets SGMC off-catalogue faults directly (scarps are
fault surface expression). Estimated SGMC cal DTI gain vs 0.0641 champion: +0.02–0.05.

**Implementation cost:** Low. Single script, ~60 lines, uses restored external rasters.

---

## H2 — Radiometric K/Th anomaly ratio + magnetic tilt derivative

**Layers:** `external/geodawn_rad_u8.tif` (airborne radiometrics), `training_features.tif`
band 1 `mag_anom` (total-field magnetic anomaly).

**Physical signature:** Hydrothermal alteration mobilises K (clay illitisation) and fixes/dissolves
Th, producing anomalous K/Th ratios; demagnetisation marks fault-related alteration zones. The
tilt derivative of the magnetic field enhances subtle buried sources. Coincident K/Th anomaly +
magnetic low = blind hydrothermal system along a fault.

**Why it catches catalogue-missing faults:** Geothermal systems are often blind (no surface
fault trace). Radiometric element ratios and magnetic tilt detect subsurface alteration without
requiring a mapped fault line.

**Differs from repo implementations:** Existing submissions use `tc` (total count) magnitude,
not K/Th ratios, and `mag_anom` amplitude, not tilt derivative. No run card uses radiometric
element ratios from `geodawn_rad_u8.tif`.

**Expected DTI improvement:** Medium-High. Directly targets geothermal conduit geometry.

**Implementation cost:** Medium. Requires band-specific radiometric processing (K, U, Th channels)
from `geodawn_rad_u8.tif`; needs band inspection to confirm channel layout.

---

## H3 — USGS ComCAT seismicity cluster depth + Qfaults distance

**Layers:** `external/usgs_comcat_geodawn.csv` (earthquake catalog), `external/gdr_qfaults_traces.csv`
(USGS Quaternary fault traces).

**Physical signature:** Clustered seismicity at 5–15 km depth defines the seismogenic fault plane.
Distance to mapped Quaternary faults excludes catalogue structures. Residual seismicity >2 km from
any mapped trace indicates a blind fault.

**Why it catches catalogue-missing faults:** Seismicity directly images active faulting regardless
of surface expression. The catalogue only includes Quaternary faults with mapped traces; seismically
active blind structures are missing.

**Differs from repo implementations:** No submission uses seismicity. `usgs_comcat_geodawn.csv` is
restored but unused in any run card.

**Expected DTI improvement:** Medium. Seismicity is a direct fault proxy but cluster depth
estimation adds uncertainty.

**Implementation cost:** Medium-High. Requires hypocentral depth binning, cluster detection,
and distance-to-trace computation.

---

## H4 — Volcanic vents + geothermal wellspring proximity

**Layers:** `external/gdr_volcanic_vents_in_footprint.csv`, `external/gdr_wellspring_in_footprint.csv`
(GDR submission 1391 geothermal data).

**Physical signature:** Recent volcanic vents and geothermal springs mark magma/heat sources
connected by fault conduits. Dots placed along vent-to-wellspring alignment vectors target the
conduit faults.

**Why it catches catalogue-missing faults:** Geothermal springs and vents are surface expressions
of blind hydrothermal systems. The connecting faults may be unmapped, especially where covered
by alluvium.

**Differs from repo implementations:** No submission uses `gdr_volcanic_vents` or
`gdr_wellspring`. These are restored but unused in run cards.

**Expected DTI improvement:** Medium. Direct geothermal indicators but sparse point data limits
coverage.

**Implementation cost:** Low-Medium. Point-to-raster rasterisation and line vectorisation.

---

## H5 — Gravity gradient magnitude + depth-to-basement edge

**Layers:** `training_features.tif` band 13 `iso_grav_anom` (isostatic gravity anomaly),
band 15 `depth_to_base_surf` (depth to basement).

**Physical signature:** The horizontal gravity gradient magnitude marks density contrasts at
faults; depth-to-basement edges mark basin-bounding faults. Combined, they highlight structural
boundaries that control geothermal fluid flow.

**Why it catches catalogue-missing faults:** Basin-bounding and intra-basin faults are often
not in the fault catalogue if they lack surface expression. Gravity gradients image the
subsurface density offset directly.

**Differs from repo implementations:** H32-C uses `iso_grav_anom` magnitude but not its gradient,
and no submission combines gravity gradient with depth-to-basement edges.

**Expected DTI improvement:** Medium. Well-established structural geophysics but gravity is a
broad, non-unique signal.

**Implementation cost:** Low. Gradient from existing band 13; depth-to-basement edge from band 15.

---

## Ranking

| Rank | Hypothesis | Expected SGMC cal DTI gain | Implementation cost | Data readiness |
|------|------------|---------------------------|---------------------|----------------|
| 1 | H1 LiDAR scarp + DEM10 chi | +0.02 to +0.05 | Low | Ready (rasters restored) |
| 2 | H2 Radiometric K/Th + mag tilt | +0.015 to +0.04 | Medium | Ready (bands need inspection) |
| 3 | H3 ComCAT seismicity + Qfaults | +0.01 to +0.03 | Medium-High | Ready (CSV restored) |
| 4 | H4 Volcanic vents + wellsprings | +0.008 to +0.02 | Low-Medium | Ready (CSV restored) |
| 5 | H5 Gravity gradient + basement | +0.005 to +0.02 | Low | Ready (bands in feature stack) |

## Validation plan

Validate H1 on the spatially-blocked holdout (`scripts/evaluate_holdout.py`,
`GEMSDOE32-HOLDOUT-v3-visible-gated`) before any submission slot. Success criterion:
fold-local HOLDOUT-DTI with paired 95% CI > 0 against the current same-evaluator repo best,
AND SGMC off-catalogue prevalence-calibrated DTI ≥ champion (0.0641), AND uniqueness
(≤70% within-3px overlap, |rho| ≤ 0.90) vs every registry raster.

No weekly submission slot is spent until H1 passes holdout validation.