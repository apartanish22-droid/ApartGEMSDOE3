# Executive summary — DOE GEMS submission decision

**Decision for this checkout: NO TIFF exists; DO NOT DOWNLOAD OR SUBMIT.** The checkout has no authorized competition rasters, cached features, shared evaluator/writer, candidate output, or complete submission registry. I therefore did not claim a new raster, a holdout result, exact uniqueness, or a competition score. No submission slot should be used.

## Nine-site historical scorecard

The historical values below are reproduced from the user-provided list, not from a submission receipt. They are explicitly **unverified user-reported claims**: they are **not `ORGANIZER-CONFIRMED`**, not `HOLDOUT-DTI`, and not independently audited score-to-file links. The table is a forensic starting point only, not a recommendation to re-upload a prior file. No reliable leaderboard-score estimate is available for any row.

| Site | Highest supplied historical claim | Submission identifier from the supplied list | File to download from this checkout | Estimated leaderboard score | Unique vs all listed sites? | Decision / source |
| --- | --- | --- | --- | --- | --- | --- |
| GEMSDOE24 | 0.2477 — unverified user-reported claim | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE24/) |
| GEMSDOE25 | 0.2600 — unverified user-reported claim | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE25/) |
| GEMSDOE27 | 0.2449 — unverified user-reported claim | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE27/) |
| GEMSDOE28 | 0.2710 — unverified user-reported claim | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE28/) |
| GEMSDOE30 | 0.2600 — unverified user-reported claim | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE30/) |
| GEMSDOE31 | 0.2708 — unverified user-reported claim | `h27-4-solo-d28-20261004-8acb75e1-nan` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) |
| **GEMSDOE32** | **0.2778 — unverified user-reported claim; largest supplied value** | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not resubmit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) |
| GEMSDOE33 | 0.2632 — unverified user-reported claim | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE33/) |
| GEMSDOE36 | 0.2750 — unverified user-reported claim | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | **None — no candidate TIFF exists here** | Not estimable | Unknown: raster bytes and full registry absent | **Do not submit.** [Site](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) |

The table’s uniqueness state is **unknown**, not “unique.” A new filename or different hash alone is not proof of the required surface-correlation and final-dot tests. The supplied top-result claims of `0.3195` and `0.4413` for the overall leaderboard conflict and have no receipt attached in this checkout; neither is treated here as a verified leaderboard maximum.

## Why GEMSDOE32 may have done well — and what can actually be concluded

The identifier and supplied comparison list suggest a sparse/dotted variant in the H19-5 / D2.8 family, but the suffix `B2` is not defined by evidence in this checkout. Do not infer its exact algorithm or attribute a causal mechanism from the name alone. From the official metric definition, each ground-truth pixel receives a true-positive credit from its best nearby prediction, linearly tapered to zero at `300 m`; the same best nearby confidence reduces its false-negative contribution. Predicted confidence also contributes a false-positive term weighted by distance from the nearest truth pixel. With `alpha=0.2` and `beta=0.8`, false negatives have a larger coefficient than false positives. A plausible metric-level rationale for strong sparse submissions is therefore complementary spatial coverage with limited redundant/off-target emission: predictions near more withheld fault segments can improve recall credit, while unnecessary mass far from faults still costs score. This is a testable rationale, not proof of what H33-2 actually did.

This is a **mechanistic hypothesis, not a causal explanation**: the TIFF, exact method code, holdout card, complete registry, and score receipt are not in this checkout. The reported score may also reflect source/evaluator differences, trial selection, or hidden-set composition. It is not possible to tell from a filename whether the model improved geology, whether the score was paired to those exact bytes, or whether it would generalize to private faults. Thus we cannot honestly claim a new candidate would exceed the reported `0.2778` or either claimed overall leaderboard value. The path to a defensible answer is independent byte-level provenance plus a matched, leakage-safe spatial holdout, followed by a separate selector decision; the holdout itself is not a leaderboard forecast.

## Candidate geological hypotheses, ranked for investigation

The initial checkout had no modeling code or experiment history; none of these mechanisms is implemented in this repo. These candidates are novel only **relative to this checkout**, not certified globally untried. The linked sibling sites have more experiments than their supplied historical-score snippets, and several report related geomorphic or geophysical variants, so a full prior-art registry search is still required before describing any as new. No method paragraph was assigned in the checkout and the required template stack/holdout tools are absent, so these are ranked proposals, not experiments. **No candidate was tested; no score improvement is projected.**

| Rank / candidate | Expected DTI improvement (qualitative, not a score projection) | Layers and target signature | Why it could reveal an unmapped fault rather than a known trace | Main non-fault mimic / leakage risk | Data availability and implementation cost |
| --- | --- | --- | --- | --- | --- |
| Highest investigation priority | Unknown; potentially modest incremental gain; no numeric forecast | **Cross-sensor contact persistence:** GeoDAWN TMI / RTP magnetic anomaly, radiometric K/eTh/eU, and gravity/conductivity if present; multi-scale directional edges/phase congruency, cross-sensor co-location, survey-seam masking. | A blind basement discontinuity may produce independent subsurface and surface-composition edges despite weak topographic expression; candidate generation uses no catalogue-distance features. | Lithologic contacts, alteration unrelated to faults, flight/tie-line artifacts, survey-resolution transitions. | Public USGS release includes gridded/GeoTIFF products [USGS](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7). Moderate-to-high harmonization cost. Distinct from a single-channel edge score; may overlap external GEMSDOE33 radiometric/conductivity experiments. Full registry audit required. |
| Second priority | Unknown; possible modest gain, high uncertainty; no numeric forecast | **Independent shallow-water geochemical corroboration:** GDR 1391 springs/wells chemistry and temperature with GeoDAWN radiometric/conductivity layers; uncertainty-aware point interpolation and disconnected cross-lithology anomaly clusters. | Thermal/geochemical anomalies may identify upflow on unmapped structures far from mapped traces; no fault-distance features in candidate construction. | Sampling/access bias, location error, lithology, non-geothermal warm waters, clustered development sites. | DOE describes free public GDR access [DOE](https://www.energy.gov/hgeo/geothermal/technical-resources); user-provided source [GDR 1391](https://gdr.openei.org/submissions/1391). Verify coverage, data license, coordinate uncertainty, and independence from known traces. Moderate cost. |
| Third priority | Unknown; low-to-moderate possible gain; no numeric forecast | **Drainage-deflection / cross-divide anomaly:** organizer DEM or USGS 3DEP DEM plus current USGS 3DHP/NHDPlus hydrography. Measure channel-bend residuals, divide crossings, and flow-direction changes after broad-slope removal. | Fault displacement or capture can perturb drainage where no mapped surface trace is available; prediction is based on drainage-network form, not proximity to known faults. | Lithology-controlled drainage, alluvial fans, shorelines, roads/culverts, DEM artifacts. | USGS 3DEP is free [3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services); USGS hydrography products [access](https://www.usgs.gov/national-hydrography/access-national-hydrography-products). NHD has been retired; prefer current 3DHP. Verify coverage first. Moderate cost; overlaps general topographic-gap work. |
| Fourth priority | Unknown; likely small/uncertain incremental gain; no numeric forecast | **Stress-compatible blind structure orientation:** official USGS focal-mechanism/stress-inversion observations plus independently generated magnetic/gravity edge orientations; compare azimuths to local SHmax with uncertainty weighting. | Mechanically favorable orientations can increase permeability potential; use stress only as a physical filter on blind geophysical candidates, never use known fault geometries as targets. | Sparse focal mechanisms, regional stress heterogeneity, interpolation error, non-fault lithologic contacts. | Public USGS dataset describes CONUS focal mechanisms and stress inversion [catalog](https://data.usgs.gov/datacatalog/data/USGS:5cf6e143e4b0d63728b9b49a), [DOI](https://doi.org/10.5066/P9BA1104). Verify local data density, error fields, and license before testing. Moderate cost; likely signal-limited.

The most actionable first scientific test is the cross-sensor contact-persistence idea because its required core geophysics is explicitly represented in the competition description and the official USGS source release is identifiable. It is **not yet cleared to run**: no lane assignment, raster data, registry, or shared evaluator is present. External data is not a blocker for a first version if the cached stack truly has the required channels; use the official USGS release only to fill documented gaps after checking overlap and usage rights. This is an experiment plan, not an estimated score.

## Validation and submission workflow

Before any model fit or placement, check assigned lane, data hashes, exact cached stack schema, and a full registry. Freeze spatial blocks and a segment-level buffer; derive every catalogue-based feature only from visible faults, mask visible faults pixel-exactly, then evaluate the pooled official DTI. Run every feature-alone leakage canary. Use the same exact evaluator for incumbent and candidate, paired uncertainty intervals, and independent confirmation. Stop on leakage, uniqueness violation, failed holdout, or unavailable registry. Do not convert holdout DTI into leaderboard-score estimates without a prevalidated calibration that is relevant to the hidden target.

The official submission format is one float32 GeoTIFF band, EPSG:32611, same grid/resolution/bounds as the template, probabilities in `[0,1]`, and null/NaN outside the bounds. The automated preflight is `scripts/validate_submission.py`; it reports only format evidence. No sample template is in this checkout, so **no format validation was performed against the competition grid**.

## Verified sources for review

| Source | Verified scope | Link |
| --- | --- | --- |
| DrivenData problem description | Task, incompleteness of known-fault labels, two prize rounds, provided layer summary, DTI and GeoTIFF submission contract | [Official competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| DrivenData competition rules | Rules and external-data eligibility should be checked before use | [Official rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) |
| Reference solution | Organizer-linked baseline implementation; local checkout does not contain it | [DrivenData reference GitHub](https://github.com/drivendataorg/gems-prize-reference-solution) |
| GeoDAWN data release | USGS/DOE airborne magnetic and radiometric data, with grid and GeoTIFF products | [USGS](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) · [DOI](https://doi.org/10.5066/P93LGLVQ) |
| 3DEP | USGS elevation product types and free-use statement; product coverage must be checked spatially | [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) |
| Hydrography | NHD retirement notice and current 3DHP access route | [USGS hydrography access](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) |
| Stress data | USGS catalog of stress-map and focal-mechanism data | [USGS data catalog](https://data.usgs.gov/datacatalog/data/USGS:5cf6e143e4b0d63728b9b49a) |
| DOE geothermal data | DOE description of public GDR resources | [DOE Technical Resources](https://www.energy.gov/hgeo/geothermal/technical-resources) · [GDR 1391](https://gdr.openei.org/submissions/1391) |
| 1 m DEM | The user-provided competition CSV of specific DEM URLs is not available locally; the listed source still needs per-tile availability/rights checks | [USGS 3DEP / National Map](https://www.usgs.gov/the-national-map-data-delivery) |

## Limitations / next-session work

- **Data access:** competition training/template files are absent. User-provided context says DrivenData's data page requires login; no authenticated download is configured in this checkout. The official public sources above are not a substitute for the competition template or labels.
- **Shared implementation:** the user-requested cached stack, `evaluate_holdout.py`, `submission_writer.py`, full raster registry, and lane assignment are all absent. Do not build an unapproved private evaluator fork; bring shared tools into the shared template first.
- **Evidence:** no score receipts, historical TIFF bytes, raster checksums, or reproducible method cards are available here. Historical scores are not verified and uniqueness is unknown.
- **Current leaderboard/quota:** inaccessible/unauthenticated in the repository review; the two overall-high-score statements conflict. Capture a dated organizer page receipt and weekly cap before selector action.
- **No generated submission:** the only truthful verdict for this checkout is negative/not ready. The validator helper is not a substitute for the missing scientific pipeline.

## Three-pass review log

| Pass | Review objective | Result |
| --- | --- | --- |
| Pass 1 | Implement the requested summary/landing page and submission-format preflight. | Completed; no competition TIFF fabricated because the required rasters and shared tools are absent. |
| Pass 2 | Review assumptions and edge cases: out-of-range values, interior NaN, finite values outside the footprint, shifted transform, dtype mismatch, and null outside encoding. | Fixed the summary table to separate historical claims from score estimates; seven synthetic GeoTIFF validator tests pass. The actual competition grid remains unavailable, so official-template validation is unrun. |
| Pass 3 | Reconcile against the official task/metric/format text, preserve score provenance, and check the site-specific historical ranking. | Confirmed the historical values are only user-supplied claims; made the GEMSDOE32 rationale explicitly hypothetical; cross-checked summary page structure and retained a negative/no-file verdict. No experiment or slot was used. |

## Required JSON run card for this review

```json
{
  "hypothesis": "No experiment: an assigned single-method lane and authorized input stack are absent.",
  "mechanism": "No prediction surface or dots were generated.",
  "named_non_fault_mimic": "Not applicable; no candidate surface exists.",
  "holdout_dti": null,
  "holdout_evaluator_version": null,
  "withheld_positive_count": null,
  "holdout_95_percent_ci": null,
  "registry_surface_rank_correlation": null,
  "registry_dot_overlap_within_3px": null,
  "raster_sha256": null,
  "validator_output": {
    "status": "NOT_RUN_NO_RASTER_OR_TEMPLATE",
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null
  },
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```
