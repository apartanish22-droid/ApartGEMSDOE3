# Repository review — 2026-10-31

## Executive decision

**NEGATIVE — DO NOT SUBMIT any artifact in this checkout.** This review produced no TIFF, ran no new scientific experiment, and used no competition slot. The repository has a strong fail-closed release stance and extensive audit records, but it does not contain an authorized method lane or the data needed to run the requested compliant experiment in this workspace. A newly generated file without those checks would be an unsupported submission, not progress toward a defensible score.

## Three-pass review

### Pass 1 — request, repo layout, and prior evidence

- Read the persistent project brief and run protocol in `README.md`; reviewed the current-status registry, latest dated repo review, nine-site audit evidence, release tooling, experiment/evaluator/writer scripts, and candidate artifacts.
- The requested nine-site comparison is already recorded in `docs/repo-review-2026-10-30.md` and `docs/research/nine-site-verification-20261030.md`. The top reported site artifact is GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, score **0.2778 OWNER-REPORT** (not tied here to an organizer receipt for the exact raster hash). It is not a new candidate: historical artifact, prior reported submission, and fails the registry overlap gate.
- That audit reports all 36 unordered pairs of the nine chosen site rasters fail the directional 70%-within-3-pixel criterion in at least one direction; 11/36 also breach |Spearman| > 0.90. GEMSDOE25 and GEMSDOE30 are identical after NaN-to-zero normalization. These are historical audit findings, not recalculated in this review.
- The supplied 0.3195 and 0.4413 leaderboard values are dated/user-supplied observations, not current verified scores. Repository evidence records a later public #1 value of 0.4544, but it too is a dated public observation, not an organizer receipt or a prediction for this project.

### Pass 2 — scientific and release-gate review

- The protocol's “single method paragraph” is not included as a distinct assigned lane. Existing README correctly says not to infer one. Consequently, no lane-specific candidate was selected or built.
- The requested data provenance matters: restored inputs and selected-site rasters are owner-maintained GitHub mirrors, not organizer-authenticated inputs. This review did not find evidence that converts them into authenticated competition data.
- The previous evidence states the full competition feature raster/cached stack and the complete registry are not available in this checkout. Therefore this review could not run the mandated fold-local, buffered whole-segment holdout, feature-alone leakage canaries, paired spatial confidence interval, or full-registry surface and final-dot uniqueness checks.
- No score projection is warranted. The historical 0.2778 submission's score mechanism cannot be established causally from the score log; the existing knowledge note appropriately describes pruning low-credit false-positive mass as a plausible, unproven explanation. A new submission cannot responsibly be claimed to beat it based on the available information.
- No external data-dependent candidate was declared viable. The earlier ranked candidate review in `docs/research/next-hypotheses-review-20261028.md` and the updated calibration discussion in `knowledge/10_calibration_finding_and_next_candidates_20261030.md` should be treated as proposal/evidence context, not fresh results.

### Pass 3 — executable checks and edge cases

Checks actually executed in this review:

| Check | Result |
|---|---|
| `python3 -m compileall -q src scripts tests` | PASS |
| `git diff --check` | PASS |
| `python3 scripts/check_release_status.py` | PASS; candidate status remains fail-closed, hashes agree, portal current, no slot used |
| `python3 -m pytest -q` | BLOCKED: system Python has no `pytest` module. No claim is made that tests passed in this review. |
| New raster / holdout / canaries / full-registry uniqueness | NOT RUN; required lane/data/assets unavailable in this checkout. |

This distinction is intentional: a prior review's test results are not fresh test results. No dependencies were installed and no competition/third-party host was contacted.

## Best-submission answer and nine-site table

The highest reported score among the requested sites is **GEMSDOE32, 0.2778 OWNER-REPORT**. It is not proof of a causal recipe or a valid score estimate for a new candidate. Its site artifact is not unique within the selected cohort under the repo's literal overlap rule and should not be resubmitted. The current target leaderboard figure is time-sensitive; do not compare a proposed model with it as though it were a score receipt.

For every site below, the exact archived filename and value are documented in `docs/repo-review-2026-10-30.md`; the listed scores are OWNER-REPORT and no new leaderboard estimate is estimable. Every archived artifact is **archive/research only**, not cleared for download-and-submit. The uniqueness result is the historical nine-file cohort check, not a full-registry audit of a new TIFF.

| Site | Highest reported score | Uniqueness vs the other eight selected sites | Submission decision |
|---|---:|---|---|
| GEMSDOE24 | 0.2477 OWNER-REPORT | FAIL | Do not submit archived file |
| GEMSDOE25 | 0.2600 OWNER-REPORT | FAIL; exact normalized duplicate of GEMSDOE30 | Do not submit |
| GEMSDOE27 | 0.2449 OWNER-REPORT | FAIL | Do not submit archived file |
| GEMSDOE28 | 0.2710 OWNER-REPORT | FAIL | Do not submit archived file |
| GEMSDOE30 | 0.2600 OWNER-REPORT | FAIL; exact normalized duplicate of GEMSDOE25 | Do not submit |
| GEMSDOE31 | 0.2708 OWNER-REPORT | FAIL | Do not submit archived file |
| **GEMSDOE32** | **0.2778 OWNER-REPORT (highest of these nine)** | **FAIL** | **Do not resubmit; not a new unique candidate** |
| GEMSDOE33 | 0.2632 OWNER-REPORT | FAIL | Do not submit archived file |
| GEMSDOE36 | 0.2750 OWNER-REPORT | FAIL | Do not submit archived file |

**New candidate score estimate: not estimable.** Do not label a holdout diagnostic as a leaderboard score. There is no generated TIFF in this review; thus there is no new file to download. The user-requested “OK to submit” signal must stay NO until the full scientific, uniqueness, exact-byte format, and separate selector gates pass.

## Follow-up priorities

1. Establish the one assigned method lane in a recorded preregistration; do not infer it from the candidate list.
2. Make the organizer-origin training features and cached feature stack available with provenance and SHA-256, or explicitly document the chosen mirror and its trust limitation.
3. Restore the complete comparison registry and use the shared `scripts/evaluate_holdout.py` and `scripts/submission_writer.py`; do not fork their behavior.
4. Run the prescribed feature-alone canaries and buffered whole-segment holdout, with catalogue-derived features rebuilt from visible faults only, exact pixel masking, pooled DTI, and paired spatial CI against the incumbent. Stop at three experiments/two hours and immediately on a literal duplicate stop.
5. Only after evidence clears those scientific gates, validate the saved bytes against the organizer template, run complete surface/final-dot uniqueness, and request separate slot-selector authorization. Preserve any negative result as a run card.
6. Run tests in a project virtual environment (`python3 -m venv .venv`, install `requirements.txt`) and record fresh output. Keep large data out of Git.

## Run card — review only

```json
{
  "hypothesis": "No experiment: no assigned method lane is available in the checkout.",
  "mechanism": "Review only; no raster or model operation.",
  "named_non_fault_mimic": "Not applicable; no candidate feature was tested.",
  "holdout_dti": "NOT RUN; evaluator version, withheld positives, and 95% CI unavailable.",
  "correlation_overlap_vs_registry": "No new raster; no new registry comparison.",
  "raster_sha256": null,
  "validator_output": "No TIFF generated; no-NaN, [0,1], CRS, shape, transform checks not applicable.",
  "submission_name": null,
  "submission_note": "Review only; no slot selected or authorized.",
  "verdict": "negative"
}
```

## Official source pointers (not fetched in this review)

- [Competition problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [INGENIOUS](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)
