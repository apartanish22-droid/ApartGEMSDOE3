# ApartGEMSDOE3 — auditable DOE GEMS research and submission gates

**Mission:** develop a scientifically defensible, genuinely new fault-prediction raster for the DOE GEMS Prize, and make it safe and simple to validate and submit. The public site puts the submission decision first. At this review, the status is **NOT READY — no new candidate GeoTIFF exists; do not download or submit a file from this repository.**

> **Session start rule:** read this README first, then `docs/research/repo-review.md`, `docs/research/focus-site-analysis.md`, `docs/research/high-score-analysis.md`, `docs/research/hypotheses.md`, and `docs/data/run-card.json`. Update the evidence and run card whenever a result changes. A negative result is a valid deliverable; a projected leaderboard score is not.

## Canonical project brief (repeated prompt consolidated)

The long task prompt has repeated passages. This section is its durable, de-duplicated operating version; it is the starting brief for future work in this repository.

1. **Objective and scope.** Focus the comparative review on GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36. Study the reported GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` result, explain only what the evidence supports, and try to improve on it only through a new, independent hypothesis. The score and causal explanation must not be invented: a site/owner claim is not an organizer receipt.
2. **Unique output.** Never copy, rename, or republish a prior TIFF as a new candidate. Historical TIFFs may be inspected for education and registry comparison only. A download link may be enabled only after the separate selector approves a candidate that passes the scientific, holdout, uniqueness, and format gates. The home page and submission guide must state clearly whether any file is safe to download and submit.
3. **Research before implementation.** Before implementing a new method, preregister three to five distinct geological hypotheses. Each must identify its exact layers, physical signature, why it may detect faults absent from the USGS/INGENIOUS catalogue, how it differs from prior repo/site methods, at least one named non-fault mimic, required official data source, and availability/coverage status. Rank by qualitative expected value and cost; do not turn a projection into a score. Test the highest-ranked candidate on the spatial holdout before considering a submission slot.
4. **Stay in one lane.** The parallel-run prompt refers to a “single method paragraph,” but this checkout did not contain such a paragraph. Do not infer or combine another run's lane. Before placement and again on final dots, compare against the full registry: stop and log a duplicate if absolute Spearman rank correlation is above `0.90` or if more than `70%` of candidate dots are within `3` pixels of one registry raster. A candidate must also be checked against current parallel work before any release.
5. **Reuse shared infrastructure.** Use the pinned shared template's feature cache, holdout evaluator, and GeoTIFF writer. Do not privately fork or silently replace these tools. If a shared tool is wrong, fix it once in the shared template and report the change. This checkout currently contains no shared template or cached feature bytes; see the repo review.
6. **Holdout protocol.** Hide whole fault segments with a spatial buffer. Derive every catalogue-based feature from visible faults only. Mask visible faults pixel-exactly for both prediction and evaluation. Score pooled distance-weighted Tversky with `alpha=0.2`, `beta=0.8`, and the `300 m` triangular kernel. Test each feature alone first; a holdout AUC above `0.90` is a leakage canary and must be investigated before training.
7. **Evidence labels.** Every score-like number must be labeled either **HOLDOUT-DTI** (evaluator version, withheld-positive count, and 95% CI) or **ORGANIZER-CONFIRMED** (copied from an organizer submission-page receipt). Public leaderboard snapshots and owner/user-reported site scores are separate provenance classes; never relabel them as receipts. Never publish a projected score as an achieved score.
8. **Submission format.** The official problem page requires one-band `float32` GeoTIFF predictions in `[0,1]`, on the training grid (CRS, resolution, bounds/shape, and transform match), with null/NaN outside the footprint. The validator must check these properties automatically and fail closed. Do not clip or rescale invalid predictions merely to pass validation; fix the upstream prediction/calibration error.
9. **Run card and budget.** End each experiment with one JSON card containing hypothesis, mechanism, a named non-fault mimic, HOLDOUT-DTI plus CI and withheld-positive count, pre-placement/final registry comparisons, raster SHA-256, validator output, submission name and a note no longer than `140` characters, and verdict `promote` or `negative`. Stop after three experiments or two hours, whichever comes first. Do not use a weekly slot without a separate selector decision.
10. **Site and usability.** Put the executive summary, file status, score provenance, uniqueness result, and submission instructions at the beginning of the site. Keep the official source links auditable. Provide an explicit no-file state when validation is incomplete. The long-term aim is a reliable, current feed and no need for a human to inspect TIFF internals.
11. **Official rule and AI disclosure.** The full DOE rules say AI use is allowed but must be disclosed in the submission narrative with the extent and how it was used. They allow up to three feedback submissions per week but require one final submission to be selected for both prize rounds; this project never selects that slot. Review eligibility and participant attestations separately.
12. **Values.** Maximize P(Win) by comparing evidence, risks, and opportunity cost; own the outcome by recording failed gates and fixing shared issues rather than hiding them. Preserve privacy: never put DrivenData credentials, tokens, or private data in Git.

## Repository review and current blockers

At the start of this session, the checkout contained only a 15-byte `README.md`; it had no model, data, tests, website, feature cache, registry rasters, evaluator, or writer. This work adds an evidence-led site and research scaffolding, **not** a trained model or a candidate raster.

The official competition data page redirected to DrivenData's login page when checked. This environment has no competition session and cannot download `training_features.tif`, `labels.tif`, `sample_submission.tif`, or `1m_DEM_links.csv`. The shared public template identified during review (`buffedlizard55-lab/57GEMSDOE`, commit `822a0ce5546c7b6749cdd82eb145b6b3e616603d`) lists the 19-band feature cache, but the source raster/cache bytes are not present in that public Git tree; the template's machine-readable preparation record also marks the feature raster unverified. Its shared `src/gems57/validate.py` and `submission_writer.py` were inspected at that pin, but neither is installed here. The validator's conservative all-finite/zero-outside policy may conflict with the official problem page's null/NaN-outside requirement; resolve this against the authorized sample/organizer guidance in the shared template, not a private fork. Consequently no compliant holdout, canary, raster uniqueness test, validator run, or new TIFF can be produced here.

**Do not substitute** a public peer site's TIFF, a synthetic zero raster, a guessed grid, or a leaderboard projection. That would violate the uniqueness and validation requirements and could repeat the `[0,1]` submission error.

## Verified public references

- [DrivenData problem description, metric, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — observed to redirect to login in this session
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DOE official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Shared 57GEMSDOE template, pinned review revision](https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [USGS National Hydrography products](https://www.usgs.gov/national-hydrography/access-national-hydrography-products)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [USGS Great Basin structural discontinuities publication](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa)

## Current public parallel-method scan (secondary evidence, not replayed here)

Two new public method records were inspected after the initial repo census so this project does not mistake their lanes for untried ideas:

- **GEMSDOE30 POOL-1** ([pinned run card](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/d21ddd9502f3c3911e8d77b8f1e6abfaadffc876/docs/research/2026-10-27-pool/run-card.json)) pools MSDB piedmont/curvilinear, CSR Laplace/Poisson/Radon, LiDAR, and raw bands in one HGB. The owner run card records candidate **HOLDOUT-DTI 0.186699** (95% CI `[0.173113, 0.200171]`, `component-holdout-v3-blockstats-20261025`, `60,988` withheld positives). Against its preregistered `pool_dense_edge` comparator it records **HOLDOUT-DTI 0.188702** (95% CI `[0.174361, 0.203224]`, same evaluator/count), with paired candidate-minus-control **HOLDOUT-DTI difference −0.002003** (95% CI `[−0.004005, −0.000065]`). The run card reports a 3-pixel overlap of `88.74%` against a pinned 394-raster registry and a duplicate stop; no TIFF was published. These owner-side measurements were not replayed in ApartGEMSDOE3.
- **GEMSDOE36 TCD-36** ([pinned run card](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/tcd36-run-card.json)) includes 10 m 3DEP morphometry and fluvial chi/steepness/knickpoints, plus spatial-context ridge consolidation. Its owner card records best arm **HOLDOUT-DTI 0.194164** (95% CI `[0.180342, 0.208343]`, `gems-segment-pooled-v1`, `60,988` withheld positives) and a literal unseparated registry overlap blocker; verdict `negative`, no upload authorization. It says a research GeoTIFF exists, but this repo does not link or revalidate it.

These **HOLDOUT-DTI** values use different evaluators and holdout protocols and are not comparable to the historical owner-reported `0.2778` competition result. They are citations to peer run cards, not independently established ApartGEMSDOE3 evidence. The fluvial hypothesis was therefore excluded from our candidate slate; POOL-1's existing feature union also remains an explicit parallel method to avoid cloning.

## Suggested review loop

1. Read the canonical brief above and the current JSON run card.
2. Verify data and tool availability before proposing experiments; never ask for or store passwords/tokens.
3. Review the official source ledger and the full registry, including parallel runs.
4. Preregister the lane and the experiment slate; do not change the slate after inspecting holdout outcomes.
5. Run the shared evaluator/writer only when the required data and template cache are actually present.
6. Re-run tests, inspect every changed file, update the run card and evidence links, and leave the site fail-closed unless every gate passes.

## Limitations to resolve before a real submission

- Authorized DrivenData data access and the actual competition rasters are absent from this workspace.
- The shared feature stack is not present; no local copy of `evaluate_holdout.py` or `submission_writer.py` is installed.
- The exact lane paragraph and the current baseline HOLDOUT-DTI (with evaluator, positive count, and CI) are not included in this repo.
- The peer-site score list has no archived organizer submission-page receipts. The site reports the values as owner/user-reported only.
- The nine-file focus-site comparison is pinned historical. A 2026-10-27 owner freshness receipt says every focus repository's main ref differed from the audit ref at its check time and that new-head TIFFs/scores were not audited. We inspected the latest GEMSDOE30 POOL-1 and GEMSDOE36 TCD-36 method cards for novelty, but did not recensus all nine new heads.
- The peer-site registry audit is published by another project and has not been independently replayed in this checkout. It reports every one of the nine historical top masks fails the stated pairwise uniqueness threshold.
- The public leaderboard is dynamic; the snapshot in `docs/data/leaderboard.json` is date-stamped and must not be mistaken for a submission receipt or private/final prize score.
- The full official rules PDF was reviewed in this session, but this repo does not assess competitor eligibility, complete the required participant attestations, or track live deadline changes. Re-check the current competition page and rules before any future upload.

**Download decision at this revision: DO NOT SUBMIT. No candidate TIFF is present.**