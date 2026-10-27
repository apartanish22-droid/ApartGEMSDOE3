# Candidate hypotheses — preregistration, 27 October 2026

These are research hypotheses, **not results or claims of a live score**. This repository
started with only an empty README; none has previously been implemented *here*. We
reviewed related public sibling descriptions, but cannot prove that no other parallel
session has tried a similar idea. Expected benefit is a qualitative priority, not a
projection. **No run is authorized until the missing assigned-method paragraph is
resolved and the literal registry preflight can pass.** A parallel run subsequently
published MRCJ, another magnetic/radiometric idea in a related family. The
composition-matched proposal predates our discovery of that run and must be
compared with it before anyone can claim methodological novelty.

| Rank | Hypothesis and input layers | Physical signature; why a fault missing from the catalogue might be found | Distinguishing operation / named non-fault mimic | Expected benefit / cost / data status |
| --- | --- | --- | --- | --- |
| 1 | **Composition-matched magnetic breaks**: GeoDAWN RTP/total magnetic intensity and radiometric K, Th, U; optionally detrended elevation. | At multiple widths, compare magnetic gradients/curvature on the two flanks of a line, but retain breaks whose radiometric composition is similar across the flanks. A buried or subdued displacement can have magnetic contrast without a surface scarp; limit the search to off-catalogue space. This is a falsifiable hypothesis, not a diagnosis. | Matching the *two flank compositions* is different from a plain global gradient or additive ridge fusion. A same-composition intrusive margin, volcanic flow boundary, survey line artefact, or magnetic lithologic contact can mimic it. | Most promising qualitative priority; medium cost. The USGS release describes public grids and flight lines; an owner-derived radiometric mirror is identified but not yet source-authenticated. Competition core is login-gated; feasibility must be verified from bytes. |
| 2 | **Drainage-deflection consistency**: 3DEP bare-earth DEM plus a hydrographic drainage network. | Look for a repeated, coherent lateral deflection of independent channels across a common line, rather than a single steep scarp; an old alluvial surface with a subtle blind-fault expression may escape the catalogue. | Channel-by-channel offset alignment is different from ordinary slope/curvature or a single fluvial-χ ridge. Stream capture, lithologic boundaries and fan channels mimic deflections. | Medium expected benefit; high cost. [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) describes free DEM products and [USGS NHD](https://www.usgs.gov/national-hydrography/national-hydrography-dataset) describes public hydrography; exact local coverage/download has not been verified. |
| 3 | **Shallow-thermal anomaly along cross-cutting structures**: INGENIOUS 2 m temperature probes; GeoDAWN magnetics and DEM. | Seek a spatially coherent warm anomaly aligned with an independently inferred structural break in otherwise low-relief terrain, where a covered fault may be missing from the map. Sparse temperature measurements alone cannot locate a fault. | Site-level, spatially cross-validated thermal association rather than a dense temperature raster or copied dots. Solar exposure, groundwater depth, seasonal temperature and anthropogenic heating can mimic it. | Uncertain benefit; high cost and spatial sparsity. The [GDR 1391 page](https://gdr.openei.org/submissions/1391) lists a public CC BY 4.0 2 m temperature-probe ZIP; contents, coverage, direct download and license compatibility with the rules still need verification. |
| 4 | **Flight-direction persistence diagnostic**: original GeoDAWN magnetic flight-line and tie-line observations, plus gridded magnetics. | Retain anomalies independently persistent across intersecting survey lines before testing whether they form a structural edge; a coherent buried fault could persist where surface evidence is weak. | Compares original line observations and aircraft geometry, not only gridded edge strength. Lithologic contacts and insufficient leveling also persist and can mimic faults. | Uncertain benefit; high cost. The [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) says flight-line CSVs are included; downloads and suitability have not been checked here. |

## Guarded evaluation plan

The first hypothesis is a **proposal only**, not an inferred assignment to a parallel
lane. Once a lane is actually supplied, freeze its parameters and registry inventory
before touching labels; restore the pinned shared feature cache and the shared
`evaluate_holdout.py` and `submission_writer.py`, without a private fork. Use spatially
blocked whole-segment hides with a buffer; build every label-derived feature from
visible labels only, mask visible labels pixel-exactly, and compute pooled DTI with
the official triangular kernel. Screen each input feature alone for two-sided AUC;
AUC above 0.90 is a leakage stop pending investigation, not a performance success.
Score the candidate and a frozen incumbent on identical folds with paired spatial
bootstrap confidence intervals and withheld-positive counts. Mapped-fault hides
are a biased proxy for expert-mapped hidden faults, so a proxy win is not a
leaderboard forecast. Check the pre-placement surface and final dots against **every**
registered raster; stop on the specified thresholds. At most three experiments.
Do not select or spend a weekly slot in this run.

## Scientific context, not evidence of success

- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and): magnetic observations help characterize subsurface structures; radiometrics relate to surface geology; flight height varies with terrain.
- [USGS Southern Gabbs Valley case study](https://pubs.usgs.gov/publication/70201803): integrates multiple exploration indicators and documents a blind geothermal system without surface hot springs or fumaroles. This does not validate any proposed predictor.
- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/): the prediction target is geological faults, not proof of an active geothermal vent.
