# ApartGEMSDOE3 — DOE GEMS research and submission audit

> **Current release decision (2026-10-28 UTC): NO SUBMISSION IS AUTHORIZED.** The newest locally recorded candidate is a research artifact, not a competition-ready recommendation. Its recorded GeoTIFF format checks pass, but the registry uniqueness protocol is violated by a registered 5-pixel calibration lattice: **98.8513% of its dots are within 3 pixels** of that raster (above the 70% lane limit). The candidate's recorded holdout results are not organizer scores. Do not spend a weekly submission slot on this file.

This repository is an auditable research portal for DOE GEMS fault-propensity mapping. The project goal is to test scientifically motivated, distinct hypotheses under spatially blocked holdout validation, avoid leakage and duplicate methods, and only release artifacts that pass every stated gate. See the durable project brief: [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md).

## Executive summary

The nine-site figures below are **OWNER-REPORT** values copied from the supplied site/submission history, not verified DrivenData receipts. They are historical live-score reports, not estimates for a new raster. The only valid estimate of current submission performance would require a preregistered, leakage-safe holdout; **HOLDOUT-DTI is not interchangeable with leaderboard DTI**.

| Site | Best reported submission (historical) | Reported leaderboard score | Candidate uniqueness / submission advice |
|---|---|---:|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | **OWNER-REPORT 0.2477** | Historical entry; do not copy or resubmit. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | **OWNER-REPORT 0.2600** | Historical entry; do not copy or resubmit. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | **OWNER-REPORT 0.2449** | Historical entry; do not copy or resubmit. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | **OWNER-REPORT 0.2710** | Historical entry; do not copy or resubmit. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | **OWNER-REPORT 0.2600** | Historical entry; do not copy or resubmit. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | **OWNER-REPORT 0.2708** | Historical entry; do not copy or resubmit. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **OWNER-REPORT 0.2778** | Highest reported score in this nine-site set; already submitted; reference only. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | **OWNER-REPORT 0.2632** | Historical entry; do not copy or resubmit. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | **OWNER-REPORT 0.2750** | Historical entry; do not copy or resubmit. |

**Best reported historical entry in this set:** GEMSDOE32's `h33-h33-2-b2…`, **OWNER-REPORT 0.2778**. This answers which supplied score is highest; it does not establish that its method caused the result, that it is the current leaderboard leader, or that a new submission will score better. Historical files are not to be copied for submission.

### Latest locally recorded candidate — research only

`H-APART3-1-CFKC-DHC` is the latest candidate in the local run record (`2026-10-27T22:52:55Z`). The TIF is present at [`docs/downloads/gemsdoe32-apart3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif`](docs/downloads/gemsdoe32-apart3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif) **for research/audit only — DO NOT SUBMIT**. This warning overrides the older candidate run card's `promote` label.

- **HOLDOUT-DTI** — `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives, 95% CI `[0.100521, 0.128472]`: pooled DTI `0.114452`.
- **HOLDOUT-DTI** — `GEMSDOE32-SGMC-CAL-v3.0`, 62,703 off-catalogue positives, 95% CI is recorded in [the run card](evidence/apart3_cfkc_dhc_run_card.json); this is a local diagnostic, not an organizer score.
- **Uniqueness gate: FAIL.** The candidate record reports **98.8513%** within 3 px of `GEMSDOE24:inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif`, exceeding the protocol's 70% limit. Calibration probes are still registry rasters under the literal protocol; they cannot be silently exempted.
- The repository's historical candidate card labels this `promote` and `ok_to_submit=true`; that conflicts with the literal lane rule and the separate-selector protocol. The corrected decision is **negative** in [`run_card.json`](run_card.json) and [`docs/repo-review-2026-10-28.md`](docs/repo-review-2026-10-28.md).
- A file-format pass only demonstrates reported CRS/shape/transform/range checks against the local template. It is not an organizer receipt, scientific validation, uniqueness clearance, or authorization to use a submission slot.

## How to submit (only after a future release is explicitly authorized)

1. Open the [competition submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/) and review its current rules and remaining weekly quota.
2. Only use a file whose current release card says `verdict: promote`, whose registry uniqueness comparisons pass literally, and for which the separate slot selector has authorized a slot. **There is no such file in this release.**
3. Upload the single-band GeoTIFF; use the exact submission name and note from that authorized card. Never infer leaderboard score from holdout metrics.

## Reproducibility and repository review

- Canonical workflow tools: [`scripts/evaluate_holdout.py`](scripts/evaluate_holdout.py), [`scripts/submission_writer.py`](scripts/submission_writer.py), and [`scripts/check_submission.py`](scripts/check_submission.py).
- Evidence and registered hypotheses: [`evidence/`](evidence/), [`registry/`](registry/), and [`knowledge/`](knowledge/).
- Detailed review and limitations: [docs/repo-review-2026-10-28.md](docs/repo-review-2026-10-28.md).
- Website executive summary: [`docs/executive-summary.html`](docs/executive-summary.html); current release status: [`docs/release-status.html`](docs/release-status.html); [machine-readable feed](docs/data/feed.json). The feed reflects checked-in evidence and deliberately does not poll DrivenData automatically.
- Trusted reference links: [DrivenData competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS project](https://gbcge.org/current-projects/ingenious/), and [official GEMS technical report](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

## Known limits

- Competition training/label/template rasters are not present in the checkout; the local `data/` folder contains manifests and logs, not the required full rasters. The competition data page requires authenticated access. Consequently, this session cannot independently rerun the full holdout, rebuild the prediction, or validate against an organizer-supplied template.
- The required Python stack was installed for this review and the automated suite ran: `85 passed, 2 skipped`. The skipped cases depend on missing competition data. The full GeoTIFF/template comparison and holdout rerun remain unavailable without the official rasters.
- GitHub-hosted site snapshots and score figures supplied by the owner are not organizer receipts. A published leaderboard view is an external score; local holdout scores are not.
- The static portal builder and prior generated pages contain stale BHGC promotion claims. The current entry pages now state the fail-closed status; the generator and CI require follow-up (see review report).
