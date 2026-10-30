# ApartGEMSDOE3 — research and submission review

> **Current decision: DO NOT SUBMIT.** No artifact has passed every release gate and received separate selector authorization. A format-valid GeoTIFF is not necessarily scientifically sound, unique, or competition-ready. No weekly slot has been used in this review.
>
> **WCHD experiment — negative, research only:** [Download the exploratory GeoTIFF](docs/downloads/apartgemsdoe3-h3-wchd-dual104-axial388-37654-20261028T224500Z-b3dbc603-zeros.tif) for audit, **not competition submission**. Its saved bytes pass range and grid checks against a hash-pinned owner mirror, not an authenticated organizer template. The literal 3-pixel overlap against the registered calibration lattice is 99.56%, above the 70% stop threshold. Multiple exploratory reruns and changes exceeded the protocol limits and continued after a duplicate stop. No score estimate or uniqueness claim is justified. See the [corrected run card](evidence/wchd_run_card.json), [recheck](evidence/wchd_literal_recheck.json), and [ledger](evidence/wchd_experiment_ledger.json).

## Persistent project brief — read before every session

Build an auditable research and submission system for the DOE GEMS fault-mapping competition, with the goal of improving the probability of a defensible leaderboard result. **Core values: Maximize P(Win) and Own the Outcome**—make evidence-led tradeoffs, treat failures as information, and own the end-to-end result. Work autonomously where evidence and tools permit; never invent evidence, live scores, data availability, or scientific certainty.

**Research priorities:** analyze the supplied best artifacts for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36; develop distinct geologic hypotheses for unmapped faults; validate them with spatially blocked, buffered hide-and-recover tests before considering any competition slot; keep a dated, source-linked research and score ledger. Do not copy prior submissions as candidates. The scores supplied by the user are `OWNER-REPORT` unless a submission-page receipt ties a score to exact raster bytes. Do not convert holdout results into a leaderboard projection without a validated calibration study.

**Parallel-run and release protocol:**

1. Define the one assigned method lane before any experiment. Compare the surface before placement and the final dots against every registry raster: stop and log a duplicate if absolute rank correlation exceeds `0.90` or over `70%` of candidate dots lie within `3 px` of any one registered raster. Apply the literal rule; do not silently exempt calibration rasters.
2. Reuse the shared cached feature stack, `scripts/evaluate_holdout.py`, and `scripts/submission_writer.py`. Hold out whole fault segments with a buffer; derive every catalogue-based feature only from visible faults and mask visible faults pixel-exactly. Use pooled DTI (`alpha=0.2`, `beta=0.8`, `300 m` triangular kernel). Fix shared-tool defects centrally.
3. Test each feature alone on holdout. Treat AUC above `0.90` as leakage until proven otherwise. Compare to a matching incumbent using the same evaluator and paired spatial confidence intervals.
4. Label each score `HOLDOUT-DTI` (evaluator version, withheld-positive count, 95% CI), `ORGANIZER-CONFIRMED` (from an organizer receipt), or `OWNER-REPORT`. A projection is never a score.
5. End each experiment with a JSON run card: hypothesis, mechanism, named non-fault mimic, holdout DTI + CI, correlation/overlap versus registry, raster SHA-256, validator output, submission name/note (note <=140 characters), and `promote` or `negative` verdict.
6. Stop at three experiments or two hours. A positive experiment is not authorization: the slot selector is separate and must honor the current weekly cap.
7. Validate the exact saved single-band GeoTIFF against the competition template: CRS, shape, affine transform, finite full-array values in `[0,1]` (including outside the footprint). Only show a submit/download CTA for a candidate that has also passed scientific, uniqueness, and selector gates.

The user-supplied prompt refers to a single assigned method paragraph, but that paragraph is not present in this checkout. Until it is supplied, do not infer or invent the lane. See the [project charter](docs/PROJECT_CHARTER.md) for the fuller durable protocol and [current-session review](docs/repo-review-current-session-2026-10-28.md) for this checkout's blockers.

## Current executive status

- [Repository review — 2026-10-30](docs/repo-review-2026-10-30.md): three-pass review, nine-site score status, validation results, blockers, and follow-up. Read this alongside the project brief at the start of each session.

- **Start here (2026-10-30):** [Nine-site verification, why 0.2778, and the submission decision](docs/research/nine-site-verification-20261030.md). No file is cleared to download or submit. Re-verified from bytes: 4 of 9 site files pass the strict finite [0,1] check; GEMSDOE30 duplicates GEMSDOE25; all 36 site pairs exceed the 70% overlap gate. Holdout DTI ranks the nine files in reverse of the owner-reported scores (Spearman ρ = -0.85, n = 9), so it is not a valid selection signal for the official off-catalogue test. Public leaderboard #1 read 2026-10-30: 0.4544 (conflicts with prompt values 0.4413 and 0.3195; flagged).
- [Executive summary and nine-site comparison](docs/executive-summary.html): no new submission is authorized; estimate for a new raster is **not estimable**. The listed historical scores are owner-reported, not confirmed receipts.
- [Why GEMSDOE32's reported 0.2778 is not explained causally](knowledge/03_why_02778_and_the_anatomy_of_the_family.md): the nested pruning sequence is consistent with removing low-credit false-positive mass, but does not prove why the score changed or predict a new score.
- [Current session repository review](docs/repo-review-current-session-2026-10-28.md) · [four-candidate research shortlist](docs/research/next-hypotheses-review-20261028.md) · [current negative run card](evidence/session_review_20261028.json).
- Current recorded candidate: `H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS`, file `gemsdoe32-apart3-unique-offcatalogue-geophys-20261028T225009Z-22727d79-zeros.tif`, submission name `H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS` (SHA-256 `8d90342de3a9d62bb718ea209ed5644cca0878eff906029dbc975da438cdcafd`), documented in [`evidence/H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS_run_card.json`](evidence/H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS_run_card.json). It is **negative**: the recorded HOLDOUT-DTI is 0.002126 [0.001567, 0.002606], canaries are missing, and the full-registry uniqueness comparison was not run. This is not authorized for download or submission.
- Earlier CTHG-DHC candidate `H-APART3-2-CTHG-DHC` (SHA-256 `9d5cab2ed8b393cd509c196961481520772bee5b1791e322e0b15cdbba696112`) also remains negative: its literal registry overlap and scientific-integrity gate fail.
- The root `run_card.json` and historical CSHD artifact `apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif` (named `APARTGEMSDOE3-CSHD-37B32D5B`, SHA-256 `65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38`) are retained as audit/education history only; no download link is provided. Its original promotion claim is withdrawn. A local format pass against an owner mirror is not submission authorization; literal registry overlap and a scientific band-mapping error fail release.

## Reproduce automated checks

Use an isolated environment; installing dependencies into the OS Python may be blocked by PEP 668.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json
.venv/bin/python scripts/check_release_status.py
.venv/bin/python scripts/build_review_site.py
# Re-verify the nine focus files from bytes (about 2 minutes; fetches 5 files from pinned GitHub refs if absent)
.venv/bin/python scripts/verify_nine_site.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite submission/apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif
# Format only (owner mirror, NOT authorization); negative candidate, do not submit
.venv/bin/python scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite docs/downloads/gemsdoe32-apart3-unique-offcatalogue-geophys-20261028T225009Z-22727d79-zeros.tif
```

The format inputs are hash-pinned owner mirrors, **not organizer-authenticated**. This review restored only the small format/label inputs needed for tests; it did not restore the large 19-band training-feature raster or cached feature stack. Therefore this environment cannot run a compliant new holdout experiment. `data/` remains the documented location for restored inputs; large files are ignored by Git.

## Official reference links

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login required), and [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [INGENIOUS project](https://gbcge.org/current-projects/ingenious/), [GDR submission 1391](https://gdr.openei.org/submissions/1391), and [EPSG:32611](https://epsg.io/32611).
- Links are pointers for review, not claims that those sites or source files were reachable or revalidated in this restricted session. See `registry/sources.json` for recorded provenance and access status.
