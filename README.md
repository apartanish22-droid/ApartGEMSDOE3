# Apart GEMS DOE 3

> **Start every session here. Current decision: NO NEW TIFF IS APPROVED TO SUBMIT.**
> The original checkout contained only an empty README. A parallel run subsequently committed a research TIFF and partial peer-mirrored data. Its earlier `promote` claim is **superseded**: the TIFF fails the registered lattice rule. No assigned lane, authenticated organizer dataset, replayed comparable baseline, or complete live registry is established. This review used no weekly slot.

[Open the executive dashboard](index.html) · [Submission guide](executive-summary.html) · [Research directions](research.html) · [Current run card](evidence/run_card.json) · [Nine-site audit](evidence/historical_audit.json)

## Project brief — read first

The original request was supplied twice with long, partly duplicated site/result lists. This section is a **consolidated operational restatement**, not a verbatim archive of every repeated line. The original conversation remains the source for its full wording.

**Goal.** Build an autonomous, auditable system for generating a **new, scientifically defensible single-band GeoTIFF** for the [DOE GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/), targeting the leaderboard without copying prior submissions. The project must make it immediately obvious whether a file can be downloaded and submitted, identify it and supply a short note, test range/CRS/shape/transform and other gates without relying on a human inspector, and show a separate executive submission guide. A local holdout is not an organizer score. Do not fabricate a forecast or call a file unique on the basis of a different name or hash.

**Focus sites.** Investigate the historical leaders from GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Provide the file, evidence class, score estimate if justified, uniqueness and authorization in the [dashboard](index.html). The user-supplied numbers are unverified unless a submission-page receipt binds the exact file to the result. Explain the GEMSDOE32 H33 result and whether a better one is possible without overstating causality. Review other sites for comparison, not as files to copy. Source data and restrictions belong in an auditable table with official links.

**Research.** Before implementing, identify and rank 3–5 distinct hypotheses, the layers and physical signatures, how each could detect previously unmapped faults, its differences from existing work, plausible non-fault mimics and data access. Validate the top assigned lane on a spatially blocked holdout and against the comparable current best before selecting a weekly slot. Negative results are deliverables. Seek verified, freely usable official sources, respecting rules, licenses and provenance. Fault detection is not proof of a geothermal vent or commercially viable reservoir. See [pre-registration](docs/research/preregistration.md) and the [source register](docs/research/data-and-sources.md).

**User's priority:** “MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.” This goal is **not yet fulfilled**; do not mark it fulfilled by relaxing the gates.

### Parallel-run protocol (retained from the request)

1. **LANE.** The lane is the single assigned method paragraph. Stay inside it. If rank-correlation with any registry raster exceeds 0.90, or more than 70% of dots fall within 3 pixels of one registry raster's dots, log a duplicate and stop. Check on the surface before placement **and** on the final dots. The cited method paragraph is absent from this request; do not silently claim an assignment.
2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Hide whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). Fix a shared tool in its template rather than keeping a private fork.
3. **LABEL SCORES.** A valid holdout is `HOLDOUT-DTI` with evaluator version, withheld positives and 95% CI; `ORGANIZER-CONFIRMED` requires a submission-page receipt. A projection is never a score. Inherited user-reported values remain explicitly **UNVERIFIED**; an organizer public leaderboard snapshot does not authenticate our files.
4. **LEAKAGE CANARY.** Test each raw and derived feature alone. AUC above 0.90 is leakage until proven otherwise.
5. **RUN CARD.** End with one JSON card containing hypothesis, mechanism, named non-fault mimic, holdout DTI + CI, registry correlation/overlap, raster SHA-256, validator output, submission name and a note of at most 140 characters, and verdict `promote` / `negative`. Missing measurements must be null, not invented.
6. **BUDGET.** Stop after at most 3 experiments or 2 hours. Do not select a real submission: a separate selector makes that decision within the actual weekly cap. A format pass or research download does not authorize upload.

**Core values.**

- **Maximize P(Win):** weigh tradeoffs and risk, and prioritize the outcome over attachment to any method.
- **Own the Outcome:** follow results end to end, act on issues within our means, and report failures and uncertainty instead of hiding them.
- **Review in three passes:** implement and verify; inspect assumptions, bugs and edge cases and fix them; re-check against the request and improve reliability and completeness. Keep sources and limitations current.

## What we verified in this initial review

- The parallel MRCJ file `apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif` exists with SHA-256 `fb4400e342e8aab8b059e067cfac8b2225b48534e46800d6efe69c2f2d9403d1`, but **DO NOT SUBMIT**: an independent exact-file audit found 100% of its 37,654 dots within 3 pixels of the registered lattice. The parallel run's 27.39% maximum covered only nine other sites. Its original `promote`/`ok_to_submit` claim is archived but superseded; [audit](evidence/parallel_mrcj_audit.json).
- The parallel run recorded **HOLDOUT-DTI 0.022070** (`gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI [0.01724, 0.02692]); this review did not replay it. Its comparison to a non-fold-rebuilt static champion does not prove improvement over a valid current best, and it is not a leaderboard score. The parallel run reports three experiments and no slot used; this review ran no experiments.
- The nine selected historical TIFFs were fetched at pinned Git commits and their Git blob identities checked; their 72 directional pair comparisons all fail the literal overlap rule. A broader [457-path inventory](registry/tiff_inventory.json) is an **index only**, not a complete novelty audit.
- The H33 raster is a pixel-exact subset of D2.8 after deleting 6,436 dots at most two pixels from the peer-mirrored catalogue. This geometry does not establish why the claimed score changed; [analysis](docs/research/h33-analysis.md).
- A registered spacing-5 lattice covers all but 6,649 of 5,167,373 mirrored footprint cells within 3 pixels. At the historical 37,654-dot budget, any placement overlaps the lattice by at least 82.34%; a smaller budget is **not** automatically a pass. Do not select lattice holes or remove the reference to game the rule.
- The peer `sample_submission.tif` has the same in-footprint values as its peer `labels.tif`. The organizer says its sample predicts absence. We did **not** authenticate either mirror with the organizer: use the mirror only for geometry, never as model features or predictions.
- The organizer specifies null/NaN outside data bounds. A fully finite zero exterior may pass a strict `[0,1]` raw-array check but is not itself evidence of compliance or portal acceptance. The cause of the user's reported rejection remains unknown.
- The public leaderboard displayed **0.4544, organizer leaderboard snapshot on 2026-10-27 around 21:20 UTC**; this is a public team score, not an artifact-linked receipt. The brief's historical 0.3195 and 0.4413 figures are not current verified highs. The selected site's 0.2778 is **USER-REPORTED / UNVERIFIED**, not organizer-confirmed.
- One peer research file has **HOLDOUT-DTI 0.194164** (peer-recorded, not replayed; `gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI [0.18034, 0.20834]). Its final dots fail the literal lattice gate; [independent exact-file check](evidence/peer_reference_audit.json). Holdout and leaderboard scores are not interchangeable.

## Reproduce this audit

Requirements: Python 3.11+, `gh` CLI with access to public GitHub, and the dependencies below. This review adds no binary TIFFs; the parallel branch already committed some peer-mirrored rasters and a blocked research TIFF. Those bytes are not authenticated organizer inputs. New raw/prepared files, credentials and caches must not be committed. The cached shared source is byte-for-byte; it is not a private fork. The specialized upstream evaluator CLI is not by itself a runnable assigned lane or a complete feature stack.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/cache_shared_template.py  # cache hash-pinned upstream source
python scripts/audit_priority.py         # fetch/verify nine peer rasters + lattice, then audit
python scripts/audit_peer_reference.py   # optional: existing peer research-only TIFF
python scripts/audit_parallel_run.py     # recheck the blocked parallel file; not a model run
python scripts/refresh_inventory.py     # pinned nine-repo TIFF path inventory, not a comparison
python scripts/refresh_inventory.py --heads  # freshness check, not an updated score feed
python scripts/build_site.py
python -m pytest
```

For format diagnostics only:

```bash
python scripts/inspect_submission.py path/to/file.tif --template path/to/organizer_sample.tif
```

This command does not modify the TIFF, run a holdout, establish official sample authenticity, certify portal acceptance or approve a slot. `--offline` uses the previously verified local cache. Without the authenticated organizer sample, the default peer-mirrored grid is an explicitly unverified proxy.

GitHub Pages serves the repository root. The dashboard checks only the nine selected historical repository heads when opened; it does not check the lattice or the wider registry, and reports unknown on errors or rate limits. A changed head requires a fresh audit, not automatic promotion. The official leaderboard link is live; scores on this site are dated evidence, not a continuously synchronized feed.

To run the optional interactive browser smoke test, install Node 20+ and the operating-system Chromium dependencies (including `libnss3`/`libnspr4`), then run `npm ci && npm run test:browser`. It serves the local static files on a test-only loopback port and mocks GitHub responses; it cannot establish live source availability.

## Next steps and access limitations

1. Resolve the missing lane/registry policy without changing the literal stop rule; the original common dot budget cannot pass the lattice bound. Do not optimize predictions around lattice gaps.
2. Obtain the authenticated organizer example, numeric feature stack, known-fault labels and DEM links with lawful access; establish provenance and licensing. The [data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) returned login in this session. There is no DrivenData account access here, and direct binary access to the user-supplied Dropbox/GDR URLs is blocked by the sandbox's network policy.
3. Reconstruct and replay a truly comparable fold-local best and a complete, current registry across parallel runs. Then run the assigned top hypothesis, canaries, surface/final checks and exact-byte validation under the budget. The separate selector must verify current weekly capacity before any upload.
4. Resolve the exterior encoding with the organizers or an authenticated validation receipt. Never imply that zero fill automatically fixes an upload error.

Official references: [problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS data catalog](https://gdr.openei.org/submissions/1391), and [the full source table](docs/research/data-and-sources.md).
