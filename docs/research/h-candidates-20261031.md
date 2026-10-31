# Five candidate hypotheses, ranked — 2026-10-31

**Status:** pre-implementation list. Every number here is a judgement or a repository fact, not a score. Expected DTI improvement is **not estimable** until a candidate is run on the holdout and the shared evaluator.

**Lane:** no method lane is assigned in this checkout or in the 2026-10-31 prompt. The paragraph the prompt refers to is absent. This list does not invent one. Any candidate below is a self-declared research run and cannot be cleared for a weekly slot until an owner assigns a lane (see the release gate in `README.md`).

## Why these candidates

The live leaderboard is dominated by one signal family. The nine focus files, the H19-5 → d2.8 → B=2 ladder, and most of the 451 registry rasters are gradient, ridge, Hessian, tilt or lineament detectors on the same few layers. Those rasters overlap heavily (all 36 focus-site pairs exceed the 70%-within-3-px gate, per `docs/research/nine-site-verification-20261030.md`). A new submission inside that family will mostly re-rank the same dots. The most useful contrarian move is a signal the codebase does not already compute.

Method for the overlap column: `grep -rniE` over `src/`, `scripts/`, `vendor/`, `knowledge/` and `docs/` (run 2026-10-31). An identifier match is a lead for code review, not proof of overlap.

## Ranked candidates

| Rank | Hypothesis | Layers (band index, name from `data/prepared_manifest.json`) | Physical signature targeted | Why it should hit an off-catalogue fault | Named non-fault mimic | Overlap with existing code (grep evidence) | Implementation cost | Expected DTI improvement |
|---|---|---|---|---|---|---|---|---|
| **1** | **H-S1 — Oriented line-integral of local magnetic spectral roll-off (fractal-texture anomaly).** | 2 `rtp` only (magnetic residual). Control: 13 `iso_grav_anom` not used; `external/acquisition_block_id_100m.tif` used only as a flight-line check. | Local radially averaged power-spectrum slope β of the detrended RTP residual in 3.2 km windows. Damage zones and brecciated corridors add high-wavenumber power, so β is locally flatter. Anomalies are integrated along 8 orientations over 2 km to make the response linear. | Fault damage zones are narrow and linear, and they sit under cover where the edge tools lose the trace. A spectral texture signal does not need a visible edge. | Magnetite-heterogeneous lithology and flight-line noise. Acquisition-block control is required. | **No spectral-slope or fractal identifier** in `src/` or `scripts/` (`grep -i "spectral slope\|power spectr\|fractal\|roll-?off"` returns nothing relevant). Local standard deviation exists only for the DEM (`src/gems32/juxtaposition.py`, 5×5 `det_elev`), which is not the same. | Low–medium (windowed FFT, about 2 minutes) | Not estimable |
| 2 | H-M1 — Magnetic–gravity co-gradient alignment (rtp × isostatic gravity). | 2 `rtp`, 13 `iso_grav_anom` | Product of gradient magnitudes times the absolute cosine of gradient direction, as in H35-C, but on the magnetic/gravity pair. | Faults that offset both fields should produce co-oriented edges in both. | Co-located intrusive contacts that carry both a magnetic and a density contrast. | **Partial overlap.** `src/gems32/h35_new.py:122–138` implements the same functional form (gradient product × |cos|) on `cond_surf` and `depth_to_base_surf`. The layer pair is new, the form is not. | Low (reuse H35-C code) | Not estimable |
| 3 | H-B — Directional semivariogram anisotropy of potential-field residuals. | 2 `rtp`, 13 `iso_grav_anom` | Along-strike versus cross-strike short-range continuity. | Faulted basement corridors elongate spatial dependence even when the edge is weak. | Aligned stratigraphy; GeoDAWN flight-line direction. | **No match** for `semivariogram` in code (one hit, in a build script that lists the idea). Proposed in `docs/research/next-hypotheses-review-20261028.md`. | Medium–high (directional statistics on the full raster) | Not estimable |
| 4 | H-D — Signed cross-front topographic asymmetry. | 12 `det_elev`, 19 `det_elev_slope` | Signed elevation asymmetry across off-catalogue edges. | Tilted range fronts keep a coherent asymmetric profile after the scarp degrades. | Aspect-controlled erosion. | **Partial overlap** with `src/gems32/juxtaposition.py` (A48-H1 JXSTEP, step-vs-ramp profiles). | Low–medium | Not estimable |
| 5 | Structure-tensor orientation entropy of the magnetic gradient. | 2 `rtp` | Low orientation entropy = coherent linear texture. | Linear faults produce low-entropy texture. | Any strongly anisotropic magnetic source. | **High overlap.** `src/gems32/features.py` (`_structure_tensor`, `coherence_s2`, `strike_cos`) and `src/gems32/h33.py` already compute structure-tensor coherence and orientation. | Low | Not estimable; expected to be redundant |

## Decision

**Implement and validate rank 1 (H-S1)** first. It is the only top-ranked idea with no existing identifier match and a different physical signal (texture, not edges). Rank 2 is cheap and reuses code, but its functional form is already used in H35-C, so it is a partial repeat. Rank 3 is the strongest untested geometry idea but costs more; it waits for the next session.

## Named limits

- A holdout win on rank 1 would not establish a leaderboard gain. The nine-site analysis found the catalogue-withheld holdout ranks the existing files in reverse of the owner-reported scores (Spearman ρ = −0.85, n = 9). The SGMC off-catalogue proxy was the closer tracker (ρ = +0.95 on the same nine files; ρ = +0.40 on 117 live-ledger rasters, CI [+0.22, +0.56]). See `knowledge/10_calibration_finding_and_next_candidates_20261030.md`.
- The SGMC proxy is a USGS State Geologic Map Compilation fault layer (Horton, San Juan & Stoeser 2017, USGS DS-1052, doi:10.5066/F7WH2N65, [source](https://ngmdb.usgs.gov/Prodesc/proddesc_105832.htm)). It is a mapped-geology proxy, not the organizer's private test set.

## Sources (manual review)

- DrivenData problem description: test set is "faults that are not contained within the current public USGS database"; metric is the distance-weighted Tversky index with α = 0.2, β = 0.8 and a 300 m triangular kernel; submissions are float32 GeoTIFF with values in [0, 1] and "data outside the bounds is null or nan" — [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (fetched 2026-10-31).
- Cross-gradient constraint, the method behind H-M1: Gallardo, L. A. & Meju, M. A. (2004), JGR 109(B3), B03311, doi:10.1029/2003JB002716 — [UWA repository record](https://research-repository.uwa.edu.au/en/publications/joint-two-dimensional-dc-resistivity-and-seismic-travel-time-inve/).
- SGMC geodatabase: Horton, J.D., San Juan, C.A., and Stoeser, D.B. (2017), USGS DS-1052 — [NGMDB record](https://ngmdb.usgs.gov/Prodesc/proddesc_105832.htm).
