# Executive summary — current nine-site review

## Release decision

**Research TIFF available: YES. OK TO SUBMIT: NO — DO NOT SUBMIT.** This is an exact artifact carried forward from the prior MRCJ run, not a new TIFF generated in this review. It is downloadable for audit/research only. Its current selector disposition is negative. Do not confuse the old run-card `verdict: promote` with a current release authorization.

| File | Evidence / score estimate | Unique vs all nine focus rasters? | Download / submit decision |
|---|---|---|---|
| [`apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif`](downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif) · SHA-256 `fb4400e342e8aab8b059e067cfac8b2225b48534e46800d6efe69c2f2d9403d1` | **HOLDOUT-DTI 0.022070** — evaluator `gems-segment-pooled-v1`, `60,988` withheld positives, 95% CI `[0.017237, 0.026923]`; recorded from the prior run card, not replayed here. **Leaderboard estimate: not estimable.** | **Passes the nine tracked historical rasters only.** Recomputed max absolute pre-placement Spearman `0.008744`; max final-dot directional overlap within `3 px` `27.39%`. This is not a global uniqueness finding. A subsequent independent exact-file audit measured **100%** overlap against the pinned registered lattice, exceeding the 70% stop threshold. The nine-site result omitted that control. | **Download for research: YES. Submit: NO.** Exterior is finite zero rather than the official null/NaN-outside format; no current-best paired holdout, complete peer registry, independent replay/C2ST, quota receipt, or selector authorization. |

Current machine decision and exact-byte audit: [`docs/data/latest-run-card.json`](data/latest-run-card.json). Original scientific run receipt: [`evidence/parallel_mrcj_original.json`](../evidence/parallel_mrcj_original.json). The prior card's 3 experiments are exhausted; this review performed no new geological experiment and used no slot.

## Nine-site historical table

The historic values and identifiers below come from the user's supplied list, not submission-page receipts. They are **unverified user-reported claims**, not `ORGANIZER-CONFIRMED` and not `HOLDOUT-DTI`. “Candidate novelty” reports the locally recomputed MRCJ TIFF against the matching tracked raster. It does **not** claim that the nine historical submissions are unique from one another.

| Site | Highest supplied historical claim | Historical identifier supplied | MRCJ candidate vs this site's tracked raster | File to download / status |
|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | 0.2477 — unverified user-reported | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | Spearman `0.007897`; overlap `26.71%` — passes the specified pairwise novelty limits | MRCJ TIFF above — research only; **DO NOT SUBMIT** |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | 0.2600 — unverified user-reported | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | Spearman `0.007106`; overlap `25.25%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | 0.2449 — unverified user-reported | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | Spearman `0.007805`; overlap `27.39%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | 0.2710 — unverified user-reported | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | Spearman `0.007238`; overlap `23.37%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | 0.2600 — unverified user-reported | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | Spearman `0.007106`; overlap `25.25%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | 0.2708 — unverified user-reported | `h27-4-solo-d28-20261004-8acb75e1-nan` | Spearman `0.007692`; overlap `23.92%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | **0.2778 — largest supplied claim** | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | Spearman `0.007761`; overlap `22.61%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | 0.2632 — unverified user-reported | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | Spearman `0.007308`; overlap `24.51%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | 0.2750 — unverified user-reported | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | Spearman `0.008744`; overlap `25.62%` — passes pairwise limits | Same MRCJ TIFF — research only; **DO NOT SUBMIT** |

The overall maxima `0.3195` and `0.4413` stated elsewhere in the prompt conflict; no dated organizer receipt was supplied, so neither is certified here. The nine reported site results are useful leads but are not a calibrated ladder for hidden-score prediction. The source pages have since advanced to newer owner research artifacts than this historical score list; those current pages also generally mark files research-only / DO NOT SUBMIT. The table above summarizes the supplied historical claims, not a current-best cross-site ranking.

### Registered lattice — independently verified stop

An independent exact-file review found **37,654 of 37,654 dots (100%)** within 3 pixels of the pinned lattice, above the 70% stop threshold. Only 6,649 of 5,167,373 mirrored footprint cells are outside the lattice neighborhood; the minimum overlap at this dot count is 82.34%. See [the audit](../evidence/parallel_mrcj_audit.json). The complete registry and pre-placement surface vs this lattice remain unchecked. Do not move dots around lattice gaps to evade the rule.

## Why GEMSDOE32's H33-2-B2 is a useful lead — not a proven causal story

The public [GEMSDOE32 PR #9](https://github.com/buffedlizard55-lab/GEMSDOE32/pull/9) describes H33-2-B2 as a **removal** variant: it removed `2,545` predictions from a `40,199`-dot base to produce a `37,654`-dot raster at a `2 px` catalogue-flank setting. That PR reports owner-side cross-validation and a **projected** value of `0.2747`; it explicitly says no organizer score existed for the artifact. The `0.2778` in the user's list is therefore not tied to an organizer receipt in this project.

The plausible metric mechanism is that removing predictions with little distance-weighted true-positive credit can reduce false-positive mass while preserving coverage of unmapped faults. The official metric's `alpha=0.2`, `beta=0.8`, and `300 m` triangular kernel make spatial coverage and proximity more important than raw dot count alone. But whether those removed dots were low-credit against the competition's hidden faults is unknowable from the filename or a local proxy. **Do not state that pruning caused the reported score, and do not treat `0.2747` as a score.** A new method could exceed the reported H33 value in principle; there is no validated evidence here that this one does.

## What the prior MRCJ run actually tested

The preceding run fixed a three-arm MRCJ slate using GeoDAWN magnetic and radiometric channels (cross-scale magnetic gradient persistence, opposed magnetic/ThK gradients, and an orthogonal U/Th-gradient junction). The named non-fault mimic was a lithologic contact or acquisition-block seam. The run-card canary measured four individual features; worst direction-invariant feature AUC was `0.5221`, below the `0.90` leakage alarm threshold. These canary figures are **AUC diagnostics**, not DTI or organizer scores.

| Arm | HOLDOUT-DTI (evaluator `gems-segment-pooled-v1`; `60,988` withheld positives; 95% spatial-block CI) |
|---|---|
| E1 magnetic-curvature persistence | `0.012958` `[0.008025, 0.018878]` |
| E2 opposed magnetic/ThK gradient | `0.021273` `[0.016446, 0.026463]` |
| E3 MRCJ junction (selected arm by point estimate in that prior run) | `0.022070` `[0.017237, 0.026923]` |
| Static H33 comparator | `0.006708` `[0.006041, 0.007405]` — **not fold-rebuilt, not paired, not promotion-grade** |

All listed `HOLDOUT-DTI` values use the same stored evaluator and withheld count. These are prior-run records, not newly reproduced results. The published report's static comparison does not establish a paired gain against the current best. No valid mapping from these catalogue holdouts to a hidden leaderboard score has been demonstrated.

## Exact artifact and validator result

The shared `src/gems/submission.py:check_variants` tool was rerun against the bundled template. It verifies one float32 band, EPSG:32611, exact sample shape/transform, `5,167,373` in-footprint cells finite and in `[0,1]`, and `37,654` positive pixels. It returns `format_valid: true` for strict in-footprint/whole-array range checks, but `official_format_compliant: false`: `7,111,787` exterior pixels are zero rather than null/NaN and the nodata tag is unset. The template is an owner mirror, not an authenticated DrivenData download, and the portal's current behavior has not been tested. This is **not OK to upload**.

The fresh selector uses `src/gems/selector.py` and returns `DO_NOT_SUBMIT`. It confirms exact filename/hash and strict range format, while refusing release because the stored card cannot establish the required paired current-best comparison, complete/current registry plus peer audit, exact-file C2ST, independent replay certificate, or live weekly quota. Some missing gates are **not assessed**, not proof that the scientific idea failed. Details are in the machine card.

## Candidate slate for a future lane (not experiments)

These are qualitative priorities, not numeric leaderboard projections. The prior three-experiment allowance has already been consumed, and no explicit method paragraph was supplied. No next candidate is authorized or claimed globally untried; first check the full experiment/method registry. Data endpoints below were checked on official source pages, but spatial coverage/feature usability for this footprint still must be confirmed.

| Rank / idea | Inputs and targeted signature | Why it might find off-catalogue faults | Non-fault mimic | Expected gain / implementation cost |
|---|---|---|---|---|
| 1. Stress-compatible blind edges | Official USGS continental stress/focal-mechanism observations plus label-free magnetic/gravity edge orientation; uncertainty-weighted angular agreement with local SHmax | Adds independent mechanical favourability to blind geophysical candidates, rather than learning distance to known fault traces | Sparse focal mechanisms, local stress heterogeneity, lithologic contacts | Potentially modest if local stress support is dense; unknown; medium cost. Official data are public per the [USGS catalog](https://data.usgs.gov/datacatalog/data/USGS:5cf6e143e4b0d63728b9b49a); test local sample density first. |
| 2. Thermal/geochemical anomaly residual | GDR 1391 springs/wells chemistry and temperature, spatially residualized by lithologic/terrain background, optionally corroborated by GeoDAWN conductivity/radiometrics | May find upflow associated with unmapped permeability pathways away from known fault traces | Sampling bias, coordinate uncertainty, non-geothermal warm water, lithology | Possible modest but highly coverage-dependent; medium-to-high cost. DOE GDR is documented as free/public [DOE](https://www.energy.gov/hgeo/geothermal/technical-resources) · [GDR 1391](https://gdr.openei.org/submissions/1391). Verify specific records/rights and overlap before use. |
| 3. Cross-catchment stream-profile breaks | Official 3DEP DEM and current 3DHP/NHDPlus hydrography; detect spatially paired knickpoints and drainage-direction discontinuities after broad-slope removal | Structural offsets/capture can persist where no obvious scarp remains; uses flow-network shape, not catalogue proximity | Lithologic drainage, alluvial fans, lake shorelines, roads, DEM artifacts | Low-to-moderate expected gain; medium cost. 3DEP is free [USGS](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services); hydrography access is documented [here](https://www.usgs.gov/national-hydrography/access-national-hydrography-products). Confirm local coverage; NHD is retired. |
| 4. Survey-boundary-invariant spectral contact test | Public GeoDAWN TMI/radiometric grids; compare cross-spectral phase/edge continuity at multiple wavelengths, explicitly mask flight/tie-line seams | Tests whether a contact is geologic and continuous across independent acquisition blocks, rather than a survey artifact | Lithologic contact, alteration unrelated to faults, levelling seams | Uncertain incremental value; high harmonization cost. Official grids/GeoTIFFs are listed by [USGS](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7); several related geophysical fusions already exist, so audit novelty first. |

No experiment should be spent until the active lane, complete comparator set, same-evaluator best, and split protocol are pinned. If outside data is required, the cited official download pages are publicly reachable; that does not prove full study-area coverage or inclusion rights for every product.

## Three-pass review and remaining blockers

| Pass | Work completed | Result |
|---|---|---|
| 1 — review/implementation | Reconciled the branch with the latest `main` research artifacts, preserved the existing MRCJ TIF as research-only, added a fresh machine review card, updated README and the visible landing page, and reused the shared validator/selector. | No new TIFF or model fit. |
| 2 — defect/edge review | Reopened the exact TIFF, reran format checks, recomputed pre-placement Spearman and final-dot overlap against all nine tracked focus rasters, and ran repository tests. | Exact-file hash matches; all nine pairwise novelty checks are below thresholds; official outside-null requirement fails; selector blocks upload. |
| 3 — requirement/source review | Cross-checked official competition format/metric and USGS/DOE sources; inspected GEMSDOE32 PR #9; corrected stale “PROMOTE” wording; kept owner claims distinct from organizer receipts. | Executive decision is explicitly **DO NOT SUBMIT**; no leaderboard forecast. |

Remaining gates: official authenticated sample-template provenance; no NaN/zero exterior policy validated against organizer acceptance; active method-lane paragraph; current same-evaluator comparator and paired CIs; full updated registry and peer comparison set; exact-file C2ST and independent replay; live quota receipt. Do not upload until every gate is resolved by automated evidence.

## Official sources

- [DrivenData competition problem, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [GEMSDOE32 PR #9, H33-2-B2 analysis](https://github.com/buffedlizard55-lab/GEMSDOE32/pull/9) — collaborator/owner research, not organizer-confirmed scoring
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) · [DOI](https://doi.org/10.5066/P93LGLVQ)
- [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [USGS stress data catalog](https://data.usgs.gov/datacatalog/data/USGS:5cf6e143e4b0d63728b9b49a)
- [DOE geothermal resource data](https://www.energy.gov/hgeo/geothermal/technical-resources) · [GDR 1391](https://gdr.openei.org/submissions/1391)
