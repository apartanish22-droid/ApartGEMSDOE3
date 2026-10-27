# ApartGEMSDOE3 — auditable GEMS submission research

> **Operating brief (read first):** Maximize the probability of a scientifically defensible result and own the end-to-end outcome. Build a unique, automatically validated, single-band GeoTIFF for the DOE GEMS fault-discovery competition; never represent a projection or owner-reported number as an organizer-confirmed score. Use whole-segment buffered hide-and-recover validation, test every feature for leakage, compare surfaces and final dots against the nine-site registry, stop after three experiments, and do not spend a weekly slot without a separate selector decision. The website must put the download decision, evidence, limitations, and submission instructions first. No manual inspection is a validation gate.

This repository implements that brief and preserves the full machine-readable evidence in [`evidence/run_card.json`](evidence/run_card.json). The original request is repetitive and contains conflicting reported leaderboard highs; this concise charter is the controlling, testable transcription rather than silently selecting one claim.

## Current result

**Candidate:** `apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif`

**Automated selector verdict: PROMOTE / OK TO SUBMIT.** This means the file passed this repository's scientific, novelty, and format gates; it is **not** an organizer guarantee. No submission slot was used.

* HOLDOUT-DTI `0.022070` (evaluator `gems-segment-pooled-v1`, 60,988 withheld positive pixels, spatial-block bootstrap 95% CI `[0.017237, 0.026923]`).
* Static H33 champion comparator on the same evaluator: HOLDOUT-DTI `0.006708`. Important: the historic method could not be rebuilt fold-by-fold, so this comparator is not promotion-grade OOF evidence.
* Maximum absolute surface Spearman versus the nine registered site winners: `0.008744` (limit `0.90`).
* Maximum final-dot overlap within 3 pixels: `27.40%` (limit `70%`).
* All-finite float32 values in `[0,1]`; CRS, shape and transform match the pinned template.
* **No leaderboard estimate is claimed.** Holdout DTI is not a leaderboard-score projection.

[Open the executive summary](docs/index.html) · [Download candidate](docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif) · [Run card](evidence/run_card.json)

## Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/run_experiments.py
.venv/bin/pytest
```

The run executes exactly three preregistered arms, writes through the shared strict writer, and does not upload anything.

## Evidence boundaries and irregularities

1. The prompt's required “single method paragraph” was absent. MRCJ was therefore explicitly preregistered in code and the run card; this must be reviewed before selector approval.
2. Scores for the nine external sites are **OWNER-REPORT** copied from their repositories/user-provided ledger, not ORGANIZER-CONFIRMED receipts.
3. The template is a hash-pinned owner mirror of the competition sample; it was not downloaded from an authenticated DrivenData session in this run.
4. The all-zero exterior variant fixes the reported strict range-check failure. The writer's `official_format_compliant` field remains false because official prose prefers NaN outside; the hard format gate passes, and the zero exterior specifically satisfies validators that reject any NaN.
5. A public leaderboard value (0.3195, 0.4413, and elsewhere 0.4437) cannot be reconciled from authenticated receipts here. None is used as a model target or score estimate.

## Official sources for manual review

* [DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/)
* [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
* [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
* [USGS GeoDAWN release (DOI 10.5066/P93LGLVQ)](https://doi.org/10.5066/P93LGLVQ)
* [USGS GeoDAWN landing page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
* [EPSG:32611](https://epsg.io/32611)

Only GitHub-hosted sources were reachable from this execution environment. DOI/DrivenData/USGS links are retained for manual review; the source manifests and exact checksums are stored under `data/external/`.
