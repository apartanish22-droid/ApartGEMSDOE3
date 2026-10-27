# Apart GEMS Lab

**Current decision: DO NOT SUBMIT.** This research review did not produce a new
GeoTIFF, run a geological experiment, choose a weekly slot, or upload anything.
[Executive scorecard and nine site briefs](https://apartanish22-droid.github.io/ApartGEMSDOE3/)
· [Submission guide](docs/executive-summary.html) · [Negative run card](docs/data/run_card.json)
· [Detailed review](docs/research/review.md) · [Four preregistered hypotheses](docs/research/hypotheses.md)
· [Three review/fix passes](docs/research/review-passes.md)

## Retained user brief (summary, not a verbatim prompt)

Investigate the DOE GEMS fault-mapping competition and the reported GEMSDOE32
H33-B2 result of 0.2778. Compare nine sites (GEMSDOE24/25/27/28/30/31/32/33/36)
and official data/scoring sources; preregister 3–5 genuinely distinct geological
hypotheses with non-fault mimics, and use a shared template, feature-by-feature
leakage canaries and buffered, whole-fault spatial holdouts against the current
comparable best. Before placement screen surface rank correlations against every
registry raster; after placement screen final dots, stopping for Spearman >0.90
or >70% within three pixels. Never copy or rename an old file into a new
submission. Reopen and validate a single-band GeoTIFF, especially finite values
inside the footprint and [0,1], band/dtype, exact CRS, shape and transform. Give
it a unique name, a note of at most 140 characters and an explicit submit/stop
decision; a separate selector controls any weekly slot. Limit the run to three
experiments or two hours, make results auditable and autonomous, produce a
GitHub Pages executive summary and nine-site review, perform three review/fix
passes, and publish through a PR/merge when access permits. Classify scores as
versioned HOLDOUT-DTI with positives and 95% CI, or ORGANIZER-CONFIRMED with a
file-linked receipt; don't treat estimates or owner claims as scores.

The original full prompt is not present verbatim in the retained conversation
context for this checkout. This section preserves the available consequential
instructions, **not** a purported exact transcript. If an exact archive is
required, the original text must be supplied again rather than reconstructed.

## Why this run stopped

- The instruction refers to a “single method paragraph below” but no assignment
  paragraph is present in the retained prompt. We do not select a lane that may
  duplicate a parallel run. The derived template feature cache, complete
  parallel registry, authenticated organizer sample and matched current-best
  holdout are also unavailable here.
- One registered lattice covers 5,160,724 of 5,167,373 mirrored-footprint cells
  within three pixels, leaving 6,649 uncovered. Any 37,654 distinct in-footprint
  dots must therefore overlap it by **at least 82.34%**, above the 70% stop
  threshold. This is a necessary bound at that budget, not proof every smaller
  candidate fails. Exempting the lattice or steering points into its holes would
  change or evade the stated protocol; we do neither.
- All 72 directed comparisons among the nine pinned historical files exceed
  70% overlap. The audit is diagnostic, not a complete registry clearance. The
  unverified 0.2778 claim lacks an organizer receipt tied to the H33-B2 hash.
  Public leaderboard leader **0.4544** was observed on 2026-10-27 21:17 UTC;
  see the [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
  for current values. That leaderboard does not identify the winning file.

### A parallel research TIFF is not cleared

While this review was running, another branch merged an MRCJ magnetic/radiometric
candidate. Its exact saved bytes pass our local format checks, but **all 37,654
of its dots overlap the registered lattice within three pixels**. Its earlier
approval compared only nine historical files and is superseded; the original
receipt is retained for provenance. Its recorded HOLDOUT-DTI 0.022070
(`gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI [0.017237, 0.026923])
was not independently replayed here, and its comparator was not fold-rebuilt.
**Research download only; DO NOT SUBMIT.**

[Research TIFF](docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif)
· [Independent exact-byte audit](evidence/mrcj_audit.json)
· [Corrected parallel run card](evidence/mrcj_current_run_card.json)
· [Original historical card](evidence/run_card.json)
· [Current selector review](docs/data/latest-run-card.json)
· [Nine-site decision packet](docs/data/nine_site_download_decisions.json)
· [Archived parallel review](docs/research/parallel-site-review-original.md)

The archived experiment entry point now stops before overwriting results or
issuing a false promotion. This review ran zero geological experiments; the
separate parallel run reports three.

## Reproduce the audit

Python 3.11, GDAL-compatible wheels, internet access to public GitHub and the
GitHub CLI `gh` are required to restore the inputs. Third-party mirror bytes are
pinned by commit and SHA-256; those hashes do **not** authenticate organizer
origin, license permission, or the reported results. This review's restored
large inputs live in ignored `.cache/`; the parallel branch had already committed
some separate mirrored TIFFs before the merge. No DrivenData credentials are used.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
# Restore the unchanged shared template locally, checking both content hashes.
python scripts/fetch_template.py
# Restore just the sample/labels/lattice and nine historical reference rasters.
python scripts/fetch_assets.py --groups core history
# Write a new, separate record; does not modify the checked-in dated audit.
python scripts/audit_prior.py --out .cache/review/reproduced-audit.json
# Independently recheck the parallel research file against nine files and lattice.
python scripts/audit_candidate.py docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif --history --out .cache/review/mrcj-audit.json
# Optional: restore the 19-band raw feature TIFF and owner radiometric mirror.
python scripts/fetch_assets.py --groups features external
python -m pytest -q
python scripts/build_site.py --check
```

The raw feature TIFF is **not** the shared template's derived cached feature
stack. The mirrored sample contains positive catalogue pixels even though the
official problem describes an all-absence sample: its identity is not
established, so it is a provisional grid/footprint reference only. See the
[manifest](registry/input_manifest.json),
[template provenance](vendor/template-provenance.json) and
[source limitations](docs/sources.html). The upstream template has no identified
license and redistribution permission has not been independently established;
its unchanged source is restored locally into ignored `vendor/gems57/`, not
committed or published by this repository. Shared evaluator/cache issues were
reported upstream, not silently forked.

To inspect an arbitrary local TIFF (not an approval):

```bash
python scripts/validate_submission.py path/to/file.tif --out .cache/review/format.json
```

The checker refuses altered/missing reference hashes and reports a conservative
all-finite, `[0,1]`, zero-outside policy in addition to the shared grid checks;
a format pass is **not** scientific validation, proof of portal acceptance,
uniqueness or approval to spend a slot. The official problem description says
outside-bounds data is null/NaN, so local all-finite diagnostics do not settle
organizer handling. The actual rejected file and portal response are required
to diagnose the user's reported range error.

## Website and automation

`site_templates/` and `scripts/build_site.py` generate the historical table,
nine file-specific briefs and CSV from `evidence/prior_audit.json` and the
dated third-party site reviews in `registry/site_review.json`. The submission
guide also renders the current nine-site fail-closed packet; regenerate that
packet with `scripts/review_current_artifact.py` before rebuilding the site.
A scheduled
GitHub Pages workflow runs checks and refreshes the public leaderboard and
source heads without logging in to DrivenData. On fetch/parsing failures it
retains the last available observation and its original time rather than
inventing a fresh number. GitHub Actions' cache provides best-effort persistence
between scheduled deployments; cache eviction can revert to the older checked-in
snapshot. Source changes trigger no automatic approval or scientific re-audit.
A public feed is not a competition submission receipt.

## Evidence classes & future work

A **HOLDOUT-DTI** is a versioned local proxy with a defined withheld count and
95% confidence interval. **ORGANIZER-CONFIRMED** requires a verbatim portal
receipt tied to the precise file. The nine supplied values are
**USER-REPORTED / UNVERIFIED**. A projection is neither kind of score. No
leaderboard forecast is justified for this run.

Next: resolve the missing method assignment and literal registry policy; obtain
and authenticate official inputs, the shared derived cache and matched
incumbent; resolve the reported shared ridge/cache defect; then freeze blocked
whole-segment folds, run the canaries and only a permitted experiment. After
both registry checks and exact-byte validation, a separate selector may decide
whether a slot is warranted. Predicting a fault is not proof of a geothermal
vent or commercial resource.
