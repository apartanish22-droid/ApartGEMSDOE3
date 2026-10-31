# Repository review — 2026-10-31

## Executive decision

**NEGATIVE — DO NOT DOWNLOAD OR SUBMIT any raster from this checkout.** No new raster was generated and no new experiment was run. There is no compliant basis for a new score estimate or for claiming a unique, high-scoring submission. No weekly submission slot was used.

This is a three-pass review of the checked-out repository and available local evidence. It does not claim to have re-fetched today's competition leaderboard, accessed the login-gated organizer data, or independently authenticated owner-mirror files. The detailed byte-level comparison of the nine named sites remains in [the 2026-10-30 nine-site verification](research/nine-site-verification-20261030.md); its reported values below retain their original evidence labels.

## Pass 1 — files, provenance, and what the nine-site table says

The repository contains the project brief in [`README.md`](../README.md), release and review pages, shared holdout and writer tools (`scripts/evaluate_holdout.py`, `scripts/submission_writer.py`), and historical artifacts. In this active sandbox, `.cache/gems_data/` currently contains only `labels.tif` and `sample_submission.tif`; the full `training_features.tif`, cached feature stack, and full registry raster cache are not present. The manifest `data/prepared_manifest.json` records expected hashes and grid metadata, but is not the underlying raster data. A separate merged 2026-10-31 session records 36 pinned files restored and verified (`data/restore_receipt.json` and [`docs/research/session-20261031-review.md`](research/session-20261031-review.md)); those cached bytes are not present in this active sandbox, so that receipt is not evidence of current local availability. This session restored only the two core format inputs from the pinned owner-mirror CI manifest; that proves hash agreement with the manifest, not organizer provenance.

| Site | Highest file recorded in the supplied site audit | Score | HOLDOUT-DTI, evaluator v3.0 (22,232 withheld positives; 95% CI) | Unique against the other eight named sites? | OK to submit? |
|---|---|---:|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | OWNER-REPORT 0.2477 | 0.0932 [0.0813, 0.1060] | No | No |
| GEMSDOE25 | `gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | OWNER-REPORT 0.2600 | 0.0967 [0.0842, 0.1095] | No | No |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | OWNER-REPORT 0.2449 | 0.0927 [0.0809, 0.1054] | No | No |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | OWNER-REPORT 0.2710 | 0.0294 [0.0250, 0.0344] | No | No |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | OWNER-REPORT 0.2600 | 0.0967 [0.0842, 0.1095] | No | No |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | OWNER-REPORT 0.2708 | 0.0305 [0.0257, 0.0361] | No | No |
| **GEMSDOE32** | **`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`** | **OWNER-REPORT 0.2778** | 0.0045 [0.0038, 0.0053] | No | No — already reported submitted; duplicate-family overlap |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | OWNER-REPORT 0.2632 | 0.0520 [0.0458, 0.0583] | No | No |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | OWNER-REPORT 0.2750 | 0.0046 [0.0039, 0.0053] | No | No |

**Score labels:** the leaderboard-like values in the score column are `OWNER-REPORT` values copied from the supplied site records; this checkout has no organizer submission-page receipt linking each exact raster hash to its score. The holdout column is `HOLDOUT-DTI`, computed in the archived nine-site verification by `GEMSDOE32-HIDE-RECOVER-v3.0`, with cluster-bootstrap 95% intervals. Those holdout values are not leaderboard predictions. The full details, bytes, strict-validator checks, and pairwise overlap statistics are in [`docs/research/nine-site-verification-20261030.md`](research/nine-site-verification-20261030.md) and [`evidence/nine_site_verification_20261030.json`](../evidence/nine_site_verification_20261030.json).

The archived cohort check found all 36 site pairs breached the directional `>70% within 3 px` uniqueness threshold in at least one direction. GEMSDOE25 and GEMSDOE30 have the same positive prediction after replacing NaN outside the footprint with zero. This is uniqueness **within the nine named files only**; the full 451-raster registry check for a new candidate is not available in this checkout. No file above is a recommended download.

## Pass 2 — scientific interpretation, hypotheses, and blockers

### Why GEMSDOE32's reported 0.2778 is highest in this cohort

The most defensible mechanism is a **plausible interpretation, not a proven causal finding**. The competition describes its test positives as faults not contained in the public USGS database and uses distance-weighted Tversky with FP weight `α=0.2`, FN weight `β=0.8`, and a 300 m triangular kernel. If a prediction is close to the known catalogue, it may add little credit on an off-catalogue test while still contributing false-positive mass. Pruning catalogue-adjacent dots can therefore raise the metric if the removed dots carry little hidden-test credit. The owner-reported sequence described in the repository is consistent with that mechanism, but the exact effect has not been isolated by a randomized or paired causal test.

**Important contrary evidence:** in the archived nine-file comparison, the hide-and-recover holdout ranks the owner-reported scores in reverse (`Spearman ρ≈−0.85`, `n=9`), while an off-catalogue SGMC diagnostic has positive association. A later archived calibration study over 117 owner-reported rasters found the hide-and-recover rank association weak and uncertain (`ρ=+0.17`, 95% bootstrap CI [−0.02, 0.34]) and the SGMC-calibrated association positive (`ρ=+0.40`, 95% bootstrap CI [+0.22, +0.56]). These are calibration diagnostics on owner-reported data, not score conversions. They do **not** support a claim that a new method will score above 0.2778.

The repository's last recorded public leaderboard observation is **0.4544** for xiaofanhu, fetched 2026-10-30; it is a dated `PUBLIC-LEADERBOARD-OBSERVATION`, not an Oct. 31 live check or a score for this project. It conflicts with older prompt values 0.4413 and 0.3195. The 0.3195 value is historical in the repository's snapshots, not the current record. See the [leaderboard evidence](../evidence/leaderboard_snapshot_20261030_fetch.json) and [irregularities ledger](../registry/irregularities.json).

### Candidate hypotheses for a later, explicitly assigned lane

These are research proposals, not validated candidates. Rank is qualitative expected information/utility versus implementation cost; numerical improvement is **not estimable**. The source registry and code search show some ideas have been registered before, so none is claimed as novel across the wider group of GEMSDOE sites. Per the parallel-run protocol, no method is selected or implemented in this review because the prompt's assigned single-method paragraph is absent and the feature raster is not present.

| Rank | Hypothesis and layers | Physical signature and why it could find unmapped fault structure | How it differs from implemented repo work / status | Mimic, data need, cost |
|---|---|---|---|---|
| 1 | **Topological intersection nodes** — competition band 12 (`det_elev`) and bands 3/9 (`tmi_hg`, `tmi_vg`); derive independent lineament skeletons. | Score robust intersections and relay-like junctions where a surface lineament crosses an independently derived magnetic edge. Intersections can focus permeability and geothermal upflow; requiring two different physical fields may reveal a blind structural junction rather than merely extending a catalogued trace. | Registered in `registry/hypotheses.json` as `ARENA49-H2-NODE` and marked not run there. The inspected feature code has multi-field concordance, but no matching topological skeleton-crossing object detector was found. This is therefore an unrun, registered idea, not a newly invented or proven method. | Drainage/channel intersections, lithologic contacts, and raster/flight-line seams. No new external data is needed beyond the competition bands; those bands and cached transforms are absent locally. Low–medium cost. Qualitative expected utility: medium-low; no DTI estimate. |
| 2 | **Cross-divide drainage-mobility asymmetry** — seamless 3DEP 10 m DEM derivatives / χ channels, with band 12 elevation and band 19 slope. | Pair headwater χ/relief across drainage divides and test for spatially coherent tilting aligned with a candidate basin-margin structure. A buried or degraded fault may tilt a horst block without leaving a strong scarp. | The concept appears as deferred `H-APART3-2C` in the CTHG preregistration; current CFKC/CSHD code uses χ and knickpoints but not the explicitly paired cross-divide statistic. Not run as specified in this checkout. | Lithologic contrasts, climate/runoff gradients, and drainage capture. Requires 3DEP-derived drainage inputs. Official source pointer: [USGS 3DEP / The National Map](https://apps.nationalmap.gov/downloader/). The official endpoint's current accessibility and exact area coverage were **not checked** in this sandbox; therefore this is blocked, not a viable validated proposal. High cost. Qualitative expected utility: low–medium; no DTI estimate. |
| 3 | **GeoDAWN radiometric ternary alteration-boundary edges** — official GeoDAWN K, eTh, and eU radiometric channels and band 6 total count, after checking channel semantics and acquisition-block effects. | Use a ternary/F-parameter contrast and nested edge persistence to target K-metasomatism or silica-leached alteration boundaries along blind hydrothermal conduits, not just local topographic scarps. | Registered as `ARENA49-H4-TERN` in `registry/hypotheses.json`, marked not run. Existing code uses other radiometric contrasts (for example, K/Th residualization); this exact ternary/F-parameter signature was not found in the inspected implementation. | Intrusive lithology, weathering, evaporite/playa effects, and survey-block calibration seams. The listed official source is [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), DOI 10.5066/P93LGLVQ (recorded in `registry/sources.json`). Direct source availability and input bytes were not revalidated in this sandbox; blocked until verified. Low–medium cost. Qualitative expected utility: low–medium; no DTI estimate. |

**Candidate gate before any run:** first obtain the assigned lane and authorized, hash-verified inputs; inspect the applicable full registry; compare the surface before placement; test every feature alone for leakage; run fold-local, buffered whole-segment hide-and-recover with visible-only catalogue-derived features and exact visible-fault masking; compare the same evaluator's pooled DTI and paired spatial CI against the incumbent; then check final dots against every registry raster. Stop on `|Spearman| > 0.90` or `>70%` within 3 px. The experiment budget is three experiments or two hours. A positive holdout result is not slot authorization.

### Why no new TIF was generated

The request requires a unique TIFF and high-scoring validation, but generating an unvalidated or repackaged prior raster would violate the stated rules. In this checkout:

- The assigned method paragraph/lane is absent.
- `training_features.tif`, cached feature stack, and full registry rasters are absent. Competition downloads require DrivenData access; direct credentials are not present, and this sandbox did not access the login-gated page.
- Only the small label/template inputs were restored from pinned owner mirrors. Their checksums match those mirrors; the source is not organizer-authenticated.
- No new feature-alone leakage canaries or full-registry preplacement/final-dot uniqueness checks can be performed without the missing data.
- A leaderboard estimate is not supportable. Existing HOLDOUT-DTI values are not converted into projected competition scores.

Accordingly, no TIF download CTA is added and no previous submission is altered or relabelled as new.

## Pass 3 — executable checks and edge cases

The first test invocation failed two template-dependent tests because `.cache/gems_data/sample_submission.tif` was absent. I then ran the repository's documented restore command using the pinned CI format manifest:

```text
.venv/bin/python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json
```

It restored `labels.tif` and `sample_submission.tif`; the cache is ignored by Git. After restoration:

- `.venv/bin/python -m pytest -q` — **119 passed, 2 skipped**, with 33 Rasterio affine `PendingDeprecationWarning`s. Two skips are not passes.
- `.venv/bin/python scripts/check_release_status.py` — **PASS**, fail-closed status, stored artifact hashes match, portal pointers current, no slot used.
- `.venv/bin/python -m compileall -q src scripts tests` — **PASS**.
- `git diff --check` — **PASS**.

No new holdout evaluator or candidate was run in this review: its required feature/cached inputs are not present locally. A separate merged session did reproduce the incumbent exactly: `HOLDOUT-DTI` 0.0045153787 [0.0038164176, 0.0052615983], evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives; see [`evidence/holdout_incumbent_recheck_20261031.json`](../evidence/holdout_incumbent_recheck_20261031.json) and [`evidence/session_20261031_run_card.json`](../evidence/session_20261031_run_card.json). The prior session's format audit reports 11/17 TIFF variants passed and six NaN variants failed the whole-array validator against the owner-mirror template; this review did not rerun that audit because the files used by it are not restored here. See [`evidence/format_audit_20261031.json`](../evidence/format_audit_20261031.json). No current live leaderboard fetch was performed.

## Suggested next work

1. Supply the method paragraph that assigns this lane; until then do not select one of the registered hypotheses by inference.
2. Restore the organizer-authenticated training raster and feature cache, or record precisely which permitted hash-pinned owner mirror is being used and keep the provenance limitation visible.
3. Restore the complete registry and run its literal preplacement/final-dot duplicate comparison before any candidate placement.
4. Reproduce the existing holdout incumbent using the canonical shared evaluator, then run at most three preregistered experiments within two hours. Use a positive/negative run card for each.
5. Keep the site fail-closed until scientific gates, exact saved-byte validation, uniqueness, and a separate weekly-slot selector all agree. Refresh the public leaderboard as a dated observation only.

## Sources for manual review

- [DrivenData competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem / metric / submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [login-gated competition data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), and [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://apps.nationalmap.gov/downloader/), [INGENIOUS project](https://gbcge.org/current-projects/ingenious/), [GDR submission 1391](https://gdr.openei.org/submissions/1391), and [EPSG:32611](https://epsg.io/32611).

Pointers above are for manual review. Except where dated repository evidence is cited, this review does not claim that a remote source was reachable or freshly revalidated on 2026-10-31.
