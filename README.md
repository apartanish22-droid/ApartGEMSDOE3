# ApartGEMSDOE3 — evidence-first DOE GEMS research

> **Persistent project starting point:** read this file before every work session. This checkout began as an empty starter and still has no competition rasters, cached feature stack, shared evaluator/writer, full registry, or prior experiments. Do not imply that a TIFF was generated, a score was measured, uniqueness was checked, or a submission was authorized when those inputs are absent.

## Mission and operating principles

The goal is to improve the probability of a scientifically credible, high-scoring submission to the [DOE GEMS Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/), while owning the end-to-end result. Optimize for **Maximize P(Win)**: spend scarce experiments and submission slots only on candidates with evidence. **Own the Outcome**: surface failures, correct tool defects in shared code, preserve negative results, and never relabel an estimate as a score.

### Required lane / parallel-run protocol

1. **Stay in the explicitly assigned method lane.** Before placement and again on final prediction dots, compare the prediction surface's rank-correlation and dot proximity against every registry raster. If absolute rank-correlation exceeds `0.90` or more than `70%` of dots fall within `3 px` of any registry raster, label it a duplicate and stop. An absent assignment or registry is a blocker; do not invent either.
2. **Reuse the shared template tools.** Use the cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`; do not create private replacement tools. Holdout means hide whole fault segments with a buffer; recompute every catalogue-derived feature from visible faults only; mask visible faults pixel-exactly; pool DTI using `alpha=0.2`, `beta=0.8`, and the official `300 m` triangular kernel. Fix shared tooling once where needed.
3. **Evidence labels.** Label every reported metric as either `HOLDOUT-DTI` (include evaluator version, withheld positive count, and 95% CI) or `ORGANIZER-CONFIRMED` (copied from a submission-page receipt). A projected score is never a score. Without receipt or valid holdout evidence, report `unknown` rather than a leaderboard estimate.
4. **Leakage canary.** Evaluate every feature alone on the holdout before trusting a model; AUC above `0.90` is presumed leakage until disproven.
5. **Automated release card.** Every run ends with a JSON card containing hypothesis, mechanism, named non-fault mimic, holdout-DTI and CI, registry correlation/overlap, raster SHA-256, validator results (no NaN inside footprint, values `[0,1]`, CRS/shape/transform match), submission name/note (note <=140 characters), and verdict `promote` or `negative`. Negative results are deliverables.
6. **Budget.** At most three experiments or two hours per run. Do not choose a real submission: promotion to a weekly slot is a separate selector step and depends on the current competition cap.
7. **No human-inspection dependency.** Build automated checks and show an unambiguous status. A technical format PASS is not scientific promotion or permission to submit.

## Submission status for this checkout

**NO TIFF is available. DO NOT DOWNLOAD OR SUBMIT anything from this repository.** There is no data or model output in this checkout, so no defensible holdout score, unique-file claim, leaderboard-score estimate, or downloadable competition submission can be produced here. Competition data requires an authenticated DrivenData download; the user-provided Dropbox links and separate GitHub Pages files are not present in this repository and have not been copied into it. Do not fabricate a raster from the reported scores.

The highest value in the user's historical list for the nine requested sites is the **GEMSDOE32** claim (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778`), but the supplied text is not a submission-page receipt. Accordingly it is **unverified owner-reported context**, not `ORGANIZER-CONFIRMED`, not `HOLDOUT-DTI`, not proof of superiority on hidden labels, and not a forecast. The user also supplied two conflicting claims for the current overall high score (`0.3195` and `0.4413`); neither has been independently verified from a receipt in this checkout. No estimated leaderboard score is published.

See [the executive summary](docs/executive-summary.md) for the nine-site table, score interpretation, ranked hypotheses, official sources, format validator, blockers, and run card.

## Submission format and safe workflow

The official competition description specifies a single-band float32 GeoTIFF, projected UTM Zone 11N (EPSG:32611), same resolution and bounds/grid as the training/template raster, confidence values in `[0,1]`, and null/NaN outside the study bounds. Derive shape, geotransform, and footprint from the organizer's sample/template; never hard-code a guessed grid. See the official [problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).

Once authorized data and an actual candidate TIFF are present, run:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/validate_submission.py path/to/candidate.tif --template path/to/sample_submission.tif
```

The CLI checks file-level format/grid/range/null constraints and emits JSON. A `PASS` means **format preflight only**. It does not establish scientific value, uniqueness, holdout improvement, permission to submit, or an organizer score. This checkout contains no template, so the validator has not been run against competition data here.

## Research guardrails

- Distinguish hidden-fault holdout evidence from the organizer leaderboard. Catalogue hide-and-recover is only a proxy and may not predict expert-discovered faults.
- Prefer explicit negative controls, spatial blocks, leakage checks, paired confidence intervals, and a frozen registry over repeated tuning on one holdout.
- The cited historical site scores are useful for prioritizing forensic review, but different source repositories/evaluators and absent score receipts make them incomparable as validated model evaluations.
- Never claim exact uniqueness from a changed name or hash. Uniqueness requires the source rasters/registry, a specified correlation calculation, and the prescribed pre-placement and final-dot checks.
- Do not use a real weekly submission slot until the separate selector confirms all gates and current quota.

## Repository structure

- `docs/executive-summary.md` — decision status, historical score claims, hypotheses, sources, blockers, and the current run card.
- `docs/index.html` — GitHub Pages landing page with the submission decision visible immediately.
- `scripts/validate_submission.py` — fail-closed GeoTIFF format preflight against an organizer template.
- `tests/` — validator tests using small synthetic GeoTIFF fixtures.

## Limitations / next work

1. Place authorized competition data in an ignored `data/` directory using the authenticated competition download; confirm exact template footprint and metadata.
2. Bring in the shared, version-pinned feature stack, evaluator, writer, frozen registry, and assigned single-method lane. This repository contains none of these yet.
3. Reproduce a segment-buffered, leakage-safe holdout and feature-only canaries; quantify uncertainty and compare against a same-evaluator incumbent.
4. Audit raster rank-correlation and 3-pixel dot overlap against the full registry before and after placement; stop on lane conflict.
5. Only after science, uniqueness, and validator gates pass, make a separate selector decision under current weekly submission limits. Preserve the page receipt as organizer-confirmed evidence.

No PR or leaderboard submission should claim a validated new candidate until these blockers are resolved.
