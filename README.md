# ApartGEMSDOE3

## Mission and working rules — read before every session

This section is the actionable, de-duplicated standing brief from the user's full request, not a verbatim archive of its repeated text. The full site-by-site history and the evidence limitations are retained in the review page.

Build an auditable, reproducible system for discovering geothermal-related faults and producing a **unique, valid DrivenData DOE GEMS GeoTIFF**. Maximize the probability of a real leaderboard improvement; own the outcome, including negative results and blockers. Do not claim a score or uniqueness without evidence.

### Mandatory research and submission protocol

1. **Method lane:** use only the method paragraph selected for this run. Check the candidate surface *before placement* and final dots against every available registry raster. If any absolute rank correlation is `> 0.90`, or `> 70%` of dots fall within 3 pixels of one registry raster, record a duplicate and stop. The supplied prompt did not actually identify a single method paragraph; do not start an experiment until a lane is explicitly discoverable in the shared template/records.
2. **Reuse shared tools:** use the shared template's cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`; do not make a private fork. Hold out whole fault segments with a buffer; derive catalogue-dependent features only from visible faults; mask those faults pixel-exactly; evaluate pooled DTI with alpha `0.2`, beta `0.8`, and a 300 m triangular kernel. Fix shared-tool defects in the shared template and report them.
3. **Label scores:** distinguish `HOLDOUT-DTI` (evaluator version, withheld-positive count, 95% CI) from `ORGANIZER-CONFIRMED` (submission-page receipt). A projection, surrogate estimate, or a score copied from an informal ledger is not a score. This repo's historical site scores below are **USER-REPORTED / UNVERIFIED**, not either of those evidence classes.
4. **Leakage canary:** score each feature alone on holdout; AUC `> 0.90` is leakage until investigated and resolved.
5. **Fail-closed validation:** before download/submission, require one-band GeoTIFF, submission CRS/shape/transform, finite values on footprint, and all predictions in `[0,1]`; also run uniqueness and holdout gates. Never label a file “OK to submit” if any required gate is missing or fails.
6. **Run card:** end each experiment with JSON recording hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlation/overlap, raster SHA-256, validator checks, submission filename and a note of at most 140 characters, and verdict (`promote` or `negative`). A blocked run must explicitly say what could not be measured.
7. **Budget:** at most 3 experiments or 2 hours per session. Do not spend a weekly submission slot on a candidate that has not beaten the current holdout best. Slot selection remains a separate step under the authenticated submission-page cap.
8. **Evidence:** cite official/primary sources for competition rules and geology; preserve reproducible commands and hashes; flag inconsistencies. Do not copy a prior TIF to satisfy the request for a new submission.

### Current checkout status (2026-10-27)

The request cites historical leaderboard thresholds of 0.3195 and 0.4413, and the focus-site history reports H33-2-B2 at 0.2778. These are prompt-provided claims, not current independently checked leaderboard values or organizer receipts. Treat them as unverified until matched to the official leaderboard or a submission-page receipt.

This checkout contains only project documentation and no source code, tests, cached features, labels, fault catalogue, submission template, registry rasters, or candidate GeoTIFFs. Consequently no holdout score, uniqueness test, or portal-format validation can be run here. **No new TIF has been generated and there is currently no file approved to download or submit.** The fail-closed review and the nine-site history are in [`docs/review-2026-10-27.md`](docs/review-2026-10-27.md); the blocked run card is [`docs/data/latest-run-card.json`](docs/data/latest-run-card.json).

The `GEMSDOE32` GitHub repository linked by the user is a separate public repository and contains implementation/evidence, but it is not checked out or wired as this repo's shared template. Its maintainers' PR #9 says that its `0.2778` / H33 result was an owner-reported live value and explicitly says no organizer score/receipt was present there. It also documents a local surrogate and evaluator disagreement. See the review for interpretation; do not treat an owner report or a projection as verified competition performance.

### Primary links for review

- [Competition overview / problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition rules and submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition data page (authentication may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN airborne survey data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [GEMSDOE32 source repository](https://github.com/buffedlizard55-lab/GEMSDOE32)
- [GEMSDOE32 PR #9: H33 decision and evidence caveats](https://github.com/buffedlizard55-lab/GEMSDOE32/pull/9)
- [Competition technical report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

## Arena values

**Maximize P(Win):** make evidence-weighted decisions, prioritize holdout and uniqueness over activity, and do not burn scarce submission slots on unvalidated ideas. **Own the Outcome:** report failure, blockers, and uncertainty clearly; improve shared tools rather than hiding defects in a fork.
