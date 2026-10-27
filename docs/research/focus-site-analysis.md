# Nine-site executive comparison: pinned historical files, not current-main winners

**Evidence class:** the table uses the pinned file/score/uniqueness records in the public GEMSDOE36 focus-nine audit. Scores are **OWNER-REPORTED/USER-REPORTED**, not authenticated organizer submission receipts. The method tags below are transcribed from artifact names and the owner-side nested-mask audit; they are not a complete independent source-code review.

**Freshness warning:** a GEMSDOE24 owner-maintained GitHub freshness receipt, checked on 2026-10-27, reports that all nine focus repositories' `main` refs differed from the refs used by its exact-file audit, and says newer-head TIFFs/scores were not audited. This page therefore compares the pinned historical files named below, not each site's latest research experiment or current best output. The [pinned freshness receipt](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a73f9ffba29260cc7708e8e0557c84c5bea7d47b/docs/data/portfolio_freshness.json) is a source-freshness record, not a scoring API.

| Site | Pinned historical file tag | Reported value | What the file/audit record supports | Uniqueness status |
|---|---|---:|---|---|
| GEMSDOE24 | H25-1 · dotted H19-5 · D1.5 | **0.2477 OWNER-REPORTED**; no receipt archived | Filename indicates a dotted/thinned H19-5-derived field with D1.5 label. The owner audit notes a close relationship to the GEMSDOE27 row. The mechanism and score attribution are not independently reproduced. | **FAIL** — owner audit reports a focus-nine 3-pixel overlap above the `70%` limit. |
| GEMSDOE25 | Dotted H19-5 · D2.8 | **0.2600 OWNER-REPORTED**; no receipt archived | H19-5-derived sparse mask. The owner nested-mask check reports the positive-pixel set is identical to GEMSDOE30's D28 row (`XOR=0`). | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |
| GEMSDOE27 | Topographic gap closure · T-V2 on D1.5 | **0.2449 OWNER-REPORTED**; no receipt archived | The filename names a topographic gap-closure step on a D1.5-tagged parent; no causal gain is established by the file name or score claim. | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |
| GEMSDOE28 | H36-1 · rung30 blind · R1 | **0.2710 OWNER-REPORTED**; no receipt archived | The artifact tag is preserved; the exact recipe is not reconstructed in this checkout. The nested audit ties the GEMSDOE31 solo row to this family. | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |
| GEMSDOE30 | D28 Poisson · 300 m · off-catalogue | **0.2600 OWNER-REPORTED**; no receipt archived | Despite a different repository and artifact name, the owner audit reports the same positive-pixel set as GEMSDOE25 D2.8. A new filename does not make a unique raster. | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |
| GEMSDOE31 | H27-4 solo · D28 | **0.2708 OWNER-REPORTED**; no receipt archived | The owner nested-mask audit reports its positive set is identical to the GEMSDOE28 solo-mask row. It is a related sparse family, not independent raster evidence. | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |
| GEMSDOE32 | H33 · H33-2 · B2 | **0.2778 OWNER-REPORTED**; no receipt archived | Highest value in the pinned nine-file audit. The owner audit describes B2 as a pruned D2.8-family mask; it is not proof of newly discovered faults or of what exact file was uploaded. | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |
| GEMSDOE33 | H33D · analog tip/stepover · R30 | **0.2632 OWNER-REPORTED**; no receipt archived | The artifact tag names an analog tip/stepover approach. Its held-out geological contribution was not independently evaluated here. | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |
| GEMSDOE36 | Andersonian geothermal PINN | **0.2750 OWNER-REPORTED**; no receipt archived | The owner nested-mask audit reports this legacy mask contains the B2 set plus `1,200` additional dots. This is a lineage claim, not a receipt-to-file verification. | **FAIL** — owner audit reports a focus-nine overlap above the `70%` limit. |

The exact values, hashes, source URLs, pairwise overlap/correlation fields and review date are machine-readable in [`../data/focus-sites.json`](../data/focus-sites.json). The owner audit's `max directed overlap vs other eight` is a secondary check: it is not a full current registry comparison, and this checkout did not download/recompute the historical rasters.

## Cross-site pattern and practical meaning

The reported historical bests cluster around sparse H19-5/H33-family emission and pruning. The owner-side audit documents several exact positive-mask relationships: GEMSDOE25 D2.8 and GEMSDOE30 D28 are identical; GEMSDOE31 and GEMSDOE28's solo variant are identical; GEMSDOE32 B2 is nested in the D2.8/solo family; and GEMSDOE36's legacy file adds dots on top of B2. This helps explain why nominally different submissions can share near-identical spatial support and fail a novelty gate. It does **not** prove which raster was uploaded or why a public/private score changed.

A plausible metric mechanism is that sparse pruning removes redundant or low-credit prediction mass while retaining fault-kernel coverage. Under the official distance-weighted Tversky index (`alpha=0.2`, `beta=0.8`, triangular `300 m` support), nearby redundant predictions may add little incremental weighted true-positive credit while false-positive mass remains costly. But this remains a hypothesis unless the exact bytes, fold-local construction and comparable holdout are verified. Over-thinning can also increase false negatives, which have the larger official coefficient.

## Latest method records reviewed separately

The historical table is not a summary of the new 2026-10-27 experiments. The latest public GEMSDOE30 POOL-1 and GEMSDOE36 TCD-36 records are reviewed in [`repo-review.md`](repo-review.md). Their internal HOLDOUT-DTI values are explicitly labeled with evaluator, withheld-positive count and confidence intervals; they use different evaluators, are not organizer scores, and are not compared to the historical `OWNER-REPORTED` table. A current-main best-of review of all nine repositories is still outstanding.

## Sources

- [GEMSDOE36 focus-nine source-integrity audit, pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/focus9-source-integrity.json)
- [GEMSDOE36 pairwise uniqueness audit, pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/focus-sites-pairwise-uniqueness.json)
- [Official DrivenData problem page and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [GEMSDOE30 current POOL-1 record, pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/d21ddd9502f3c3911e8d77b8f1e6abfaadffc876/docs/research/2026-10-27-pool/run-card.json)
- [GEMSDOE36 current TCD-36 record, pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/tcd36-run-card.json)

**Decision: none of these historical files is approved for this repo's submission download.** The current project has no candidate TIFF and has not used a slot. See the single canonical JSON [run card](../data/run-card.json).
