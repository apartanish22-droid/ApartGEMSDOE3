# Repository review — 2026-10-31

**Decision: DO NOT SUBMIT any file from this checkout.** This is a repository/release review, not a model experiment. No new GeoTIFF was created, no score was estimated, and no competition slot was used. The method paragraph that should assign this parallel session's single lane is absent from the prompt. I will not invent a lane or relabel an untested raster as unique.

## Executive answer

- **Best among the nine requested sites:** GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, reported as **0.2778 (OWNER-REPORT)**. No organizer submission receipt tying this score to the exact raster bytes is in the repository. It is an already-submitted previous artifact, so do not resubmit it.
- **Can this repository claim it can beat 0.2778?** No. It is scientifically possible, but there is no new candidate with a validated holdout result, a complete registry uniqueness pass, and selector approval. A new live-score estimate is **not estimable** from the evidence here.
- **Uniqueness among the nine:** none of the nine is unique under the repository's literal rule. The archived byte audit reports all 36 pairs exceed the 70% dot-overlap threshold in at least one direction. In addition, the prompt's protocol says to stop a candidate if *any* one registered raster breaches either threshold; passing only the nine-site subset would not prove full-registry uniqueness.
- **Downloadable file cleared for submission:** none. The historic GeoTIFFs are audit artifacts, not submission recommendations. Do not convert a prior TIFF to zero-outside or otherwise re-encode it to evade the portal range error; that would still be a copy of an earlier prediction.

## Nine-site executive table

The site-reported leaderboard values below are **OWNER-REPORT**, copied from the supplied/site audit; no organizer receipt is present here. Each is a historic best, not a score estimate for a new raster. Uniqueness findings are **GEOMETRY** from the repository's archived byte audit, not score evidence. The audit verifies pinned raster bytes and reports all site pairs fail the literal overlap rule.

| Site | Historic best file (reference only; do not resubmit) | Reported result | New-score estimate | Unique vs the other eight? | Cleared file to download? |
|---|---|---:|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | OWNER-REPORT 0.2477 | Not estimable | No | None |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | OWNER-REPORT 0.2600 | Not estimable | No | None |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | OWNER-REPORT 0.2449 | Not estimable | No | None |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | OWNER-REPORT 0.2710 | Not estimable | No | None |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | OWNER-REPORT 0.2600 | Not estimable | No | None; same prediction as GEMSDOE25 after NaN→0, per audit |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | OWNER-REPORT 0.2708 | Not estimable | No | None |
| **GEMSDOE32** | **`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`** | **OWNER-REPORT 0.2778** | Not estimable | No | **None — prior submission; do not resubmit** |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | OWNER-REPORT 0.2632 | Not estimable | No | None |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | OWNER-REPORT 0.2750 | Not estimable | No | None |

Reproduction/evidence pointers: [`docs/research/nine-site-verification-20261030.md`](research/nine-site-verification-20261030.md), [`evidence/nine_site_best_files_audit.json`](../evidence/nine_site_best_files_audit.json), [`evidence/nine_site_verification_20261030.json`](../evidence/nine_site_verification_20261030.json), and [`scripts/audit_nine_site_best.py`](../scripts/audit_nine_site_best.py). The historical audit is the evidence used here; it was not recomputed during this review.

### Why GEMSDOE32 was highest in the supplied nine-site list

The repository's best-supported *mechanistic explanation*, not a proven causal attribution, is that the GEMSDOE32 family thinned dense ridge candidates and removed catalogue-adjacent pixels. In the official problem framing, the target is new faults absent from the public USGS catalogue; catalogue-adjacent predictions can therefore spend false-positive mass without covering new truth. The official DTI uses α = 0.2 for false positives and β = 0.8 for false negatives, so removal of redundant false-positive mass is a plausible benefit. This is a metric-based rationale, not proof that this exact pruning caused the reported score.

Evidence and caveats:

- The archived nine-file analysis reports the GEMSDOE32 raster has 37,654 positive pixels and 69.8% of its dots are beyond 1 km from the catalogue (**GEOMETRY**; see the nine-site verification report). Its reported 0.2778 remains **OWNER-REPORT**.
- **HOLDOUT-DTI**, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives, 95% cluster-bootstrap CI: GEMSDOE32 = 0.004515 [0.003816, 0.005262] (historical incumbent record `evidence/holdout_incumbent_gemsdoe32_20261030.json`). This is a catalogue-segment hide-and-recover diagnostic, not a leaderboard score.
- **HOLDOUT-DTI**, evaluator `GEMSDOE32-SGMC-CAL-v3.0`, 62,703 withheld off-catalogue positives, 95% CI: GEMSDOE32's prevalence-calibrated diagnostic = 0.064121 [0.056730, 0.071649]. This proxy is also not an organizer score. It does not establish the causal reason for 0.2778.
- The nine-site analysis reports score ordering is strongly associated with the off-catalogue proxy but reversed against the catalogue hide-and-recover diagnostic (n=9). This is a small, related-family comparison and is not an independent prospective validation.
- GEMSDOE32 and GEMSDOE36's off-catalogue diagnostic intervals overlap substantially. Their OWNER-REPORT score difference does not establish which physical ingredient produced the higher live value.
- All nine files are highly related by the saved-pixel audit. Lineage, split noise, and selection effects remain plausible alternatives. No score receipts or public ranking confidence intervals were found.

Accordingly, 0.2778 is a useful incumbent reference—not a reliable score forecast, not an independently verified receipt, and not evidence that an arbitrary different raster will score higher.

## Candidate hypotheses for a future, lane-authorized run

These are **unvalidated hypotheses**, ranked qualitatively by expected decision value relative to implementation cost. No numerical DTI gain is asserted. The exact data-layer names and indices were read from the locally restored `training_features.tif` metadata (owner mirror; SHA-256 pinned in `registry/data_manifest.json`), while existing-code overlap was checked by search and source inspection. A hypothesis' not-yet-implemented transform is not proof of scientific novelty or publication priority.

| Rank | Candidate and specific layers | Physical signature; why it could find an unmapped fault | Named non-fault mimic | Difference from existing code / evidence | Expected value; cost |
|---|---|---|---|---|---|
| 1 | **Euler structural-index-1 solution clustering** — band 14 `tmi`; derive horizontal/vertical derivatives from this field. | Retain low-residual N≈1 Euler solutions in a preregistered depth interval and identify persistent linear clusters. Buried fault-related magnetic sources can lack a mapped surface scarp; the transform targets source geometry rather than another surface ridge. | Mafic dikes and intrusive contacts can generate similar magnetic source solutions. | `src/gems32/tmspi.py` implements local-wavenumber / SPI contact estimation explicitly for Euler N≈0, not an N≈1 Euler solver. The N≈1 idea is already preregistered but not run in `knowledge/10_calibration_finding_and_next_candidates_20261030.md`; it is not new to the repository's written research record. No exact N≈1 implementation was found in the inspected source tree. | **Highest test priority, medium expected value; medium implementation cost.** The current raster and label inputs suffice to run a computational holdout; no new external layer is required for that test. Any map-based attribution of dikes remains an open follow-up, not a gate bypass. |
| 2 | **Directional semivariogram anisotropy of geophysical residuals** — band 2 `rtp` and band 13 `iso_grav_anom`; detrend each field before local statistics. | Compare short-range along-azimuth and cross-azimuth semivariance at multiple scales. An elongated fracture/basement corridor may have directional continuity even when no single-pixel edge is prominent, potentially identifying buried structural trends. | Flight-line striping, gridding/interpolation seams, or aligned lithologic fabrics. | Existing code has gradients, structure tensors, anisotropy, and multiscale filters; no direct directional-semivariogram implementation was located in the inspected code search. This is an exact-transform distinction only, not broad conceptual novelty. | **Low-to-medium expected value; medium-high cost** (many local directional windows and robust controls). |
| 3 | **Signed magnetic–gravity edge displacement persistence** — magnetic band 2 `rtp` or band 14 `tmi`; gravity bands 13 `iso_grav_anom` and 18 `iso_grav_anom_hg`. | Detect separate field edges, estimate their signed separation along the local edge normal, then require displacement to persist across scales. A faulted basement boundary can separate shallow magnetic and deeper gravity responses under cover. | Unfaulted intrusions, source-depth contrasts, and differing filter/transfer functions can produce apparent edge offsets. | The repo has cross-field concordance and potential-field transforms (e.g. `mdrc.py`, `h36_tdr_pds.py`, `spcp.py`), but no exact signed inter-field edge-displacement persistence transform was located by the search. This candidate is adjacent to existing multi-physics work and has substantial duplication risk. | **Low-to-medium expected value; medium cost.** |

No candidate was run in this review. The highest-ranked Euler proposal is not authorized for implementation until the owner supplies the session's actual single-method paragraph and the remaining shared feature/cache and full-registry prerequisites are verified. Candidate 1 can be evaluated without new external data, but feature-only leakage canaries, fold-local hide-and-recover, matched paired uncertainty, surface uniqueness, and final-dot uniqueness still must all run. A holdout improvement alone would not authorize a slot.

## Three-pass review and verification

### Pass 1 — scope and evidence inventory

- Read the repository README, project charter, current-status record, run cards, executive summary, research notes, nine-site audit artifacts, source registry, release scripts, and tests.
- Checked that the repository already contains a durable research shortlist and a nine-site byte/holdout report; avoided duplicating or treating them as fresh calculations.
- Read the local 19-band raster metadata and confirmed the five layer mappings used above. Core bytes restored from the pinned owner mirror during review: `training_features.tif`, `labels.tif`, `existing_faults.tif`, and `sample_submission.tif`; restore script reported SHA-256 matches. This proves mirror consistency only, **not organizer authentication**. The `existing_faults.tif` and `labels.tif` mirror entries have the same SHA-256; treat that irregularity as a warning and do not infer independent provenance.

### Pass 2 — automated checks and release safety

- `.venv/bin/python -m pytest -q`: **119 passed, 2 skipped**, 33 Rasterio affine pending-deprecation warnings. The first attempt failed two tests because the ignored sample template was absent; after restoring core inputs by pinned hash, the complete run passed. The skipped tests remain skipped; no claim is made that every optional integration was exercised.
- `.venv/bin/python scripts/check_release_status.py`: **PASS**, meaning recorded candidates remain fail-closed, hashes are consistent, the portal status is synchronized to the existing negative candidate, and no slot is recorded as used. This is not a scientific promotion or authorization.
- Read `scripts/check_submission.py` and its release tests. Format/range checks are necessary but insufficient; a PASS against the owner mirror cannot establish identity with an organizer-provided template or scientific suitability.
- Did not execute a new holdout experiment, create a new submission raster, touch a slot, or alter model code. These are deliberate safety decisions because the method lane is absent and the complete registry is not locally restored.

### Pass 3 — original-request and edge-case audit

- The executive table clearly identifies each historical file, evidence class, non-estimable new score, uniqueness result, and explicit absence of an approved download.
- The top reported site file is not described as a new submission; the duplicate/lineage issue and overlap stop rule are stated plainly.
- The candidate list names bands, physical signatures, potential off-catalogue rationale, non-fault mimics, implemented-code distinctions, qualitative rank, cost, and validation limits.
- The portal error about range `[0,1]` is not diagnosed from assumption. Existing documentation records that several historic rasters contain NaNs outside the footprint and that the competition page reportedly permits outside-footprint null/NaN; this review did not access the submission form or establish the actual error cause. Do not edit old files to bypass it.
- The official public leaderboard has **not** been re-fetched for this review. The latest stored observation in the reviewed documentation is dated 2026-10-30; it is historical context, not a claim about the live 2026-10-31 leaderboard.

## Irregularities and blockers

1. **Assigned lane absent (blocking):** the protocol refers to one method paragraph, but the prompt contains no identifiable single method paragraph. The durable charter also says not to infer it.
2. **Incomplete full-registry inventory (blocking uniqueness):** the focus-site archive covers the nine named sites, but the 451-raster duplicate-gate manifest is not restored in this environment. No new surface or final-dot comparison can pass the full literal rule.
3. **Owner-mirror provenance (blocking official authentication):** core inputs were SHA-256 verified against the repository manifest, but originate in owner-maintained GitHub mirrors, not an authenticated DrivenData download. The DrivenData data page is login restricted.
4. **No prospective candidate result:** no new leakage canaries or fold-local holdout comparison were run; no claim of beating 0.2778 is supported.
5. **Historical score evidence class:** site scores are OWNER-REPORT unless an organizer receipt ties a score to the exact raster hash. No such receipt is in the repository.
6. **State freshness:** `registry/current_status.json` and parts of the static site still cite the 2026-10-28 candidate status. This review does not alter that experimental source-of-truth card; it records no new candidate. A future site refresh should surface this 2026-10-31 review and the last-known leaderboard timestamp without implying a live fetch.
7. **Input irregularity:** manifest metadata says the mirrored `existing_faults.tif` is byte-identical to `labels.tif`. Do not use that file as independent evidence or as an independent catalogue feature source.

## Follow-up, ordered to maximize decision quality

1. Record the actual single method paragraph in the repository before any new experiment; do not infer it from a candidate list.
2. Restore/rebuild the shared feature cache and restore the full registry (or demonstrate an equivalent full-registry, hash-verified scan) before uniqueness claims.
3. Authenticate the competition inputs against organizer downloads where possible; retain hashes and distinguish those bytes from owner mirrors.
4. Under the authorized lane, preregister exactly the allowed experiment count and run the feature-only leakage canaries before model selection. If G1 is authorized, test the band-14 N≈1 Euler field alone first, then the shared fold-local evaluator with a buffer and visible-only catalogue features.
5. Re-run surface uniqueness before point placement and final-dot uniqueness after placement against the full registry; stop at either threshold breach.
6. Validate exact saved TIFF bytes against the authenticated template and `[0,1]` requirements. Keep new-score estimate as “not estimable” unless a pre-registered calibration study supports a defensible conversion.
7. Only after all gates pass, use a separate selector decision within the live weekly cap. A positive research run is not slot authorization.

## Trusted-source review pointers

These are official/reference links for manual source review; this session did not fetch the external pages, so this document does not claim they were live-verified today.

- [DrivenData competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [DrivenData data page (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN survey data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [DOE/GDR submission 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611](https://epsg.io/32611)
- [Tversky index background](https://en.wikipedia.org/wiki/Tversky_index) (general reference; competition metric definition is the DrivenData page)

## Run card — review only (final)

```json
{
  "hypothesis": "No model hypothesis tested in this repository review; highest-priority unrun proposal is band-14 TMI Euler structural-index-1 clustering.",
  "mechanism": "Not tested. Proposed mechanism: clustered, persistent N≈1 source solutions may map buried fault-related magnetic structure.",
  "named_non_fault_mimic": "Mafic dikes or intrusive contacts can generate similar magnetic source solutions.",
  "holdout_dti": null,
  "holdout_dti_label": "No new HOLDOUT-DTI run; no new withheld-positive count or CI.",
  "correlation_overlap_vs_registry": "No new surface or final-dot comparison; full registry unavailable locally; fail closed.",
  "raster_sha256": null,
  "validator_output": "No new raster generated; no format-validation claim.",
  "submission_name": null,
  "submission_note": "Review only; no new submission raster or slot used.",
  "verdict": "negative"
}
```
