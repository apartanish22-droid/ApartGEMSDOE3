# ApartGEMSDOE3 — geothermal fault discovery

> **DO NOT SUBMIT: no candidate is currently authorized.** Both existing research TIFFs pass a local format check against a pinned owner mirror, but fail the required literal all-registry uniqueness rule. A successful format check is not a submission decision. No weekly submission slot was used in this review.
>
> [Executive summary and submission guide](docs/executive-summary.html) · [Audit evidence](evidence/release_recheck_20261028.json) · [Research and next steps](knowledge/09_release_recheck_and_hypotheses_20261028.md)

## Starting charter — read before working

Maximize the probability of a defensible competition result; own the outcome end to end. Build a reproducible, auditable system, not confident-looking scores. Use only verified, appropriately licensed data, document limitations and official sources, prevent leakage and false uniqueness claims, and make any submission decision obvious. The user asked for the full prompt in this README; this is an operational summary, **not a verbatim archive**.

Follow the parallel-run protocol: stay in the assigned method lane; stop on >0.90 surface rank-correlation or >70% directional 3-pixel dot overlap with **any** registry raster; reuse the shared cached feature stack, evaluator and writer; use buffered whole-segment hide-and-recover with all catalogue features derived from visible faults; run feature-only AUC leakage canaries; stop at three experiments or two hours; and leave a JSON run card. A weekly-slot selector is a separate step. Do not report projections as scores or label an owner assertion as an organizer receipt.

## Executive summary

The following are **user-reported historical scores**, not verified submission-page receipts, and do not establish that these named files are uniquely eligible for resubmission. Names are historical IDs from the request, not independently verified downloadable filenames. No current or future score can be reliably estimated from them. See the linked site for its own material; we did not modify external repositories.

| Site | Historical best reported ID | User-reported score | Unique / file to submit now |
|---|---|---:|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | h25-1-dotted-h19-5-d1-5 | 0.2477 | Historical; do not resubmit |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | dotted-h19-5-d2-8 | 0.2600 | Historical; do not resubmit |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | topo-gap-closure-t-v2-on-d1-5 | 0.2449 | Historical; do not resubmit |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | h36-1-rung30-blind-r1 | 0.2710 | Historical; do not resubmit |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | d28-poisson300m-offcat-44090 | 0.2600 | Historical; do not resubmit |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | h27-4-solo-d28 | 0.2708 | Historical; do not resubmit |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | h33-h33-2-b2 | 0.2778 | Historical; do not resubmit |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | h33d-analog-tip-stepover-r30 | 0.2632 | Historical; do not resubmit |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | anderson-geothermal-pinn-38854 | 0.2750 | Historical; do not resubmit |

Among the user-provided figures, GEMSDOE32 is highest of these nine. Its reported progression is consistent with thinning redundant nearby predictions and masking known faults, but the receipts do not prove causation or performance on unknown faults. A score above it is possible but unproven; holdout scores cannot be substituted for organizer scores.

## Research-only artifacts — not eligible for upload

- [BHGC TIFF](docs/downloads/apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif), SHA-256 `ba092640a4f776e3a22c8af1a5fe503487d4fa3f2277020a6e8268fd08e0797a`.
- [CFKC TIFF](docs/downloads/apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif), SHA-256 `afbfee1f46d6d3ca16297904cadf29d9cf9327d2ec5519e37f472c85bfaec065`.

Each is finite and [0,1] on the whole array and matches the pinned mirror's CRS, shape and transform. BHGC has 99.7450% and CFKC 99.8513% of dots within three pixels of a registered calibration lattice: both exceed the 70% limit. This lattice is dense, so overlap does not imply the same geology, yet the explicit rule has no exemption. A future change of policy must be explicit, not automatic.

## Reproduce this review

Install `requirements.txt` in a virtual environment. The pinned mirror files are described in `registry/data_manifest.json`; the core training raster and feature caches are not restored in this checkout. Run `scripts/restore_data.py` in an environment allowed to access the sources, or use the official competition data, and verify their provenance. Given the template and lattice paths:

```sh
python scripts/audit_release.py --template PATH_TO_SAMPLE --registry PATH_TO_LATTICE \
  docs/downloads/apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif \
  docs/downloads/apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif
python -m pytest -q
python scripts/build_site.py
```

The local check compares only one registered raster; it **never** issues a submission authorization. Historical runner scripts are disabled because their former gate exempted dense rasters. The [research report](knowledge/09_release_recheck_and_hypotheses_20261028.md) records four untested ideas, code/data concerns, and the next steps. Current leaderboard, authenticated competition files, assigned lane, shared-template provenance, verified surface and complete peer registry remain unresolved. See also the [parallel review](docs/review-2026-10-28.md). No new TIFF or estimated leaderboard score was created this session.

Official reference: [competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) · [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
