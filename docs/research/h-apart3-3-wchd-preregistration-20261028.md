# WCHD retrospective research note — not a valid preregistration

**Decision: negative / do not submit.** The method was self-selected without the assigned lane paragraph; parameters were revised after looking at holdout outcomes, and work continued after a duplicate stop. The session exceeded the protocol budget. The initial document and positive claims should not be treated as a preregistration or as validation. See [the corrected ledger](../../evidence/wchd_experiment_ledger.json), [run card](../../evidence/wchd_run_card.json), and [literal overlap recheck](../../evidence/wchd_literal_recheck.json).

## Ideas for future consideration, not tested as independent hypotheses

These ideas overlap prior work, so novelty is unverified. Rank is qualitative and not a predicted leaderboard score. External data availability and provenance must be verified before any proposed new experiment.

| Priority / cost | Layers and proposed signature | Why it might find a hidden fault; competing explanation | Difference to investigate |
|---|---|---|---|
| 1 / medium | Gravity anomaly and depth-to-basement; compare gradient positions across upward-continuation scales. | A buried density contrast might mark a basement fault; lithologic contacts and dikes also create contrasts. | Compare explicitly against `src/gems32/fbgr.py` and prior WCHD experiments. Continuation is not proof of fault dip. |
| 2 / medium | Radiometric K/Th, magnetic field, electrical conductivity; condition alteration anomalies on survey block and terrain. | Alteration might occur along a permeable structure, but soils, lithology and acquisition seams are alternatives. | Compare against `src/gems32/trhv.py` and `src/gems32/fbgr.py`; do not assume quantized K/Th is a physical ratio. |
| 3 / high | DEM and drainage-derived quantities; paired basin/divide asymmetry along range fronts. | A long-lived front may affect drainage even when covered; climate and variable erosion can do the same. | Compare with `src/gems32/cfkc.py`; explicit paired divides would need a documented implementation. |
| 4 / high | Satellite InSAR deformation gradients, plus groundwater context. | Faults may affect subsidence patterns; pumping and atmosphere are important non-fault mimics. | NASA/JPL [ARIA](https://aria.jpl.nasa.gov/) and [Alaska Satellite Facility](https://asf.alaska.edu/) are potential official sources; coverage, licensing and access have not been verified in this sandbox. Deferred, not a viable-ready input. |

Official context: [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [DOE GDR 1391](https://gdr.openei.org/submissions/1391). Apart from the GitHub reference, these sources were not independently accessed in this environment; links are for manual verification, not evidence that a specific derived layer is authentic.
