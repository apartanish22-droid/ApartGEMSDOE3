# Repository review and evidence audit

**Review date:** 2026-10-27 UTC
**Repository:** `apartanish22-droid/ApartGEMSDOE3`, branch `arena/11bf9a2f-apartgemsdoe3`
**Scope:** local checkout, official competition pages, public shared-template metadata, and the published owner-side nine-site registry audit. No competition binary data was downloaded.

## Executive findings

| Area | Finding | Consequence |
|---|---|---|
| Local checkout at start | Only `README.md` (15 bytes) was tracked. No code, tests, model, inputs, feature cache, registry, evaluator, writer, or TIFF existed. | This session cannot reproduce any previous candidate or holdout score from local files. The new files in this branch are research/site scaffolding, not a trained pipeline. |
| Competition data | The official DrivenData data URL redirected to the login page. No authenticated competition session is present. | `training_features.tif`, `labels.tif`, `sample_submission.tif`, and `1m_DEM_links.csv` are unavailable in this checkout. No local-format comparison or submission can be made. |
| Shared infrastructure | The public shared template is `buffedlizard55-lab/57GEMSDOE`, pinned in its published vendor metadata to `822a0ce5546c7b6749cdd82eb145b6b3e616603d`. It has evaluator, writer, validator source, and cache metadata, but none is installed in this checkout. | No private evaluator, writer, or validator was created. The shared code and cached feature bytes have not been run here. The pinned validator's whole-array finite/[0,1] and zero-outside checks may conflict with the official problem page's null/NaN-outside requirement; resolve this in the shared template against the authorized sample/organizer guidance, not in a private fork. |
| Template data inconsistency | At the pinned template, `docs/data/feature_cache.json` lists a 19-band cache and an expected feature-source SHA. `data/official/training_features.tif` is absent from the public Git tree; `docs/data/data_preparation.json` records `sha256: null`, `bytes: null`, `verified: false`, and `all_pins_verified: false`. The template `data/README.md` also describes a historical restoration in an untracked working environment. | The public repository does not make the feature bytes available; historical restoration text is not evidence that this checkout has the cache. A hash string alone cannot validate the data. |
| Focus-site score claims | The published `GEMSDOE36` focus-nine audit labels the nine historical scores OWNER-REPORTED/USER-REPORTED and says no authenticated submission-page receipt is archived. | We can report the values only with that provenance; none is ORGANIZER-CONFIRMED. |
| Historical uniqueness | The same owner-maintained pairwise audit reports all nine top rasters fail the specified pairwise uniqueness rule. Its report says every site's minimum directed three-pixel overlap against the other eight exceeds the 70% threshold. | None of the old top TIFFs is an acceptable unique file under the supplied rule. This audit has not been independently replayed in this checkout. |
| Highest reported site value | Among the nine values supplied by the user and present in that owner audit, GEMSDOE32 H33-B2 is the highest reported value. It remains unconfirmed without a receipt and does not pass the pairwise novelty gate. | It is a study/reference artifact only, **not** a recommendation to submit or re-submit. |
| Current official leaderboard | The official public leaderboard page, fetched on 2026-10-27, displayed a public leader above the `0.4413` and `0.3195` figures repeated in the prompt. The page is dynamic and is not a submission-page receipt or private/final prize score. | The prompt's “current” values are stale/contradictory. The current public snapshot is stored with provenance in `docs/data/leaderboard.json`; do not use it as a model estimate. |
| Candidate file | No new TIFF was generated. | The status is **DO NOT DOWNLOAD OR SUBMIT**. A synthetic or copied TIFF would be unsafe and would violate the uniqueness/holdout requirements. |

## Focus-site audit source

This project uses the following public owner-maintained evidence files as *secondary research records*, not as official contest receipts:

- [GEMSDOE36 focus-nine source-integrity audit](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/focus9-source-integrity.json)
- [GEMSDOE36 pairwise uniqueness audit](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/focus-sites-pairwise-uniqueness.json)

The reports document pinned source URLs, SHA-256 values, reported score provenance, and pairwise raster comparisons. They explicitly limit the inference: byte/set identity does not prove which bytes were uploaded or why the organizer score changed. Our table in `docs/data/focus-sites.json` transcribes those report fields; it does **not** assert an independent local TIFF calculation.

**Freshness:** an owner-maintained [GEMSDOE24 source-freshness receipt](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a73f9ffba29260cc7708e8e0557c84c5bea7d47b/docs/data/portfolio_freshness.json), checked on 2026-10-27, records all nine repository `main` refs as different from the exact-file audit refs used in that snapshot and states that new-head TIFFs/scores were not audited. This repo inspected the latest available GEMSDOE30 POOL-1 and GEMSDOE36 TCD-36 run cards as lane-novelty evidence, but did not re-audit every current head or replace the pinned historical nine-file comparison. The table is therefore a **historical focus-nine baseline, not a claim about each repository's newest best research output**.

## Current parallel-method records (checked after the initial repo census)

These are public run-card reports from other repositories, cited for lane novelty only. **They were not reproduced in ApartGEMSDOE3 and are not organizer receipts.** The two evaluator versions differ, so the results must not be compared directly to one another or to an organizer leaderboard score.

- **GEMSDOE30 POOL-1**: [run card pinned at `d21ddd9`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/d21ddd9502f3c3911e8d77b8f1e6abfaadffc876/docs/research/2026-10-27-pool/run-card.json). It pools MSDB piedmont/curvilinear, CSR Laplace/Poisson/Radon, LiDAR and raw bands in one HGB. The owner record reports candidate **HOLDOUT-DTI 0.186699**, 95% CI `[0.173113, 0.200171]`, evaluator `component-holdout-v3-blockstats-20261025`, `60,988` withheld positives. Its preregistered `pool_dense_edge` comparator is **HOLDOUT-DTI 0.188702**, 95% CI `[0.174361, 0.203224]`, same evaluator and count; the paired candidate-minus-control is **HOLDOUT-DTI difference −0.002003**, 95% CI `[−0.004005, −0.000065]`. The run card therefore fails its predeclared promotion gate against this comparator, despite beating `msdb_edge`. It also reports final-dot overlap `88.74%` against one entry in its pinned 394-raster registry, above the `70%` threshold; verdict negative and no TIFF published. **No POOL-1 experiment was run here.**
- **GEMSDOE36 TCD-36**: [run card pinned at `7edcc9b`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/tcd36-run-card.json). Its method includes 10 m 3DEP morphometry, fluvial chi/steepness/knickpoints and spatial-context ridge consolidation. The owner card reports best-arm **HOLDOUT-DTI 0.194164**, 95% CI `[0.180342, 0.208343]`, evaluator `gems-segment-pooled-v1`, `60,988` withheld positives; its paired gain vs its B0 is separately documented there. It passes several focus-nine checks but fails its literal unseparated registry-overlap gate (reported `99.35%` against a calibration lattice), so the card says `negative` and not approved to submit. It records a research GeoTIFF; this project does not link or independently revalidate that file.

The HOLDOUT-DTI protocols differ, and neither value is comparable to the historical organizer-test claims. These records narrow the novelty space: do not repeat POOL-1's pooled feature union or TCD-36's LiDAR/fluvial-chi family. They do not establish that the remaining AEM candidate is novel—the competition band's provenance, full registry, and actual data must still be checked.

## High-score and uniqueness conclusions

1. The available evidence supports a **plausible** explanation for H33-B2: sparse thinning/pruning can improve the distance-weighted Tversky ratio if it removes redundant low-marginal-credit prediction mass while retaining coverage of hidden positives. That is a mechanism consistent with the reported nested masks, not proof of why a particular organizer score occurred.
2. The official metric uses a triangular kernel with `300 m` support and `alpha=0.2`, `beta=0.8`; the `beta` false-negative penalty exceeds the `alpha` false-positive penalty. Dense nearby predictions do not necessarily add proportional true-positive credit because the official weighted counts use maxima over nearby predictions/truth, while emitted prediction mass can still contribute false-positive cost.
3. The owner-side audit reports that the D2.8 GEMSDOE25 and GEMSDOE30 masks have zero XOR (same positive-pixel set), that the GEMSDOE32 H33-B2 mask is nested within the D2.8/solo family, and that the GEMSDOE36 historical mask adds points over the H33-B2 set. These are audit-reported raster comparisons, not an organizer hash-to-score crosswalk.
4. The latest public GEMSDOE36 run card also tests a fluvial-chi/knickpoint/3DEP family. Therefore a generic LiDAR-channel/knickpoint idea was screened out from this session's hypothesis slate rather than repeated.
5. A score higher than the reported H33-B2 value is possible in principle, but this checkout provides no valid HOLDOUT-DTI evidence for a new method. No score projection is offered.

Detailed scientific interpretation and source caveats are in [`high-score-analysis.md`](high-score-analysis.md). Candidate ideas and availability checks are in [`hypotheses.md`](hypotheses.md).

## Verified official facts and source links

- The [official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) says the task is to identify geological faults, describes the distance-weighted Tversky metric, and specifies the GeoTIFF submission format.
- The official [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirected to a DrivenData login page during this review.
- The official [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is dynamic. Its public score is not an authenticated receipt tied to a raster SHA-256 in this repo.
- The official [GEMS Rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) governs prize requirements. Check the current page and rules before any eventual upload.
- The public [shared 57GEMSDOE template](https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d) includes `evaluate_holdout.py`, `submission_writer.py`, and `src/gems57/validate.py`; its cache metadata does not supply the source/cache bytes in this checkout.
- USGS pages document [GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services), and [hydrography access](https://www.usgs.gov/national-hydrography/access-national-hydrography-products). The presence of an official source page does not prove a particular product overlaps the contest grid.

## Irregularities flagged

- **Leaderboard values conflict by date:** the prompt gives both `0.3195` and `0.4413` as “current”; the official public page was higher when fetched on 2026-10-27. Treat those prompt values as dated claims, not live state.
- **Submission score provenance:** the nine historical site values are not backed by archived organizer submission-page receipts in the cited owner audit.
- **Uniqueness is not implied by unique names:** the pairwise owner audit reports all nine historical top rasters exceed the stated three-pixel overlap threshold against at least one other site.
- **Template-cache provenance:** the public template's restoration narrative and its machine-readable `data_preparation.json` differ in present availability/verification. There is no feature raster/cache file in the pinned Git tree.
- **Hydrography version:** USGS says NHD was retired and 3DHP is the current program. A candidate relying on NHD must pin the historic version or use 3DHP after compatibility review.
- **Participant-side rules not assessed:** the full official rules PDF was reviewed, including the AI-use disclosure and single-final-submission provisions, but this repo cannot verify eligibility or complete the registered competitor's attestations. Re-check the live rules/page and account requirements before any upload.
- **No local validator result:** without the official sample grid and a candidate raster, `[0,1]`, nodata footprint, CRS, shape, transform, SHA, and uniqueness cannot be marked pass.

## Decision

**Negative / fail closed.** No experiment, holdout, AUC canary, surface placement, final-dot test, or validator run was performed. No slot was used. No TIFF is linked for download. The current JSON evidence card is [`../data/run-card.json`](../data/run-card.json).
