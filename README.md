# ApartGEMSDOE3 — DOE GEMS fault-propensity research

> **Decision: DO NOT SUBMIT.** There is no current candidate that has passed the literal uniqueness, science-integrity, format/provenance, and promotion gates. The current candidate is research/audit-only; do not treat a download or a holdout score as submission approval. No competition slot was used in this review.

## Start every project session here

Read this README, the [project charter](docs/PROJECT_CHARTER.md), [current release status](registry/current_status.json), and the current evidence card [`evidence/apart3_cthg_dhc_run_card.json`](evidence/apart3_cthg_dhc_run_card.json) before touching experiments or submissions. Then reread the user's current session prompt: it remains the full source of task-specific requirements and may assign a lane not captured in this durable summary. The charter records the operational requirements without copying repeated prompt text verbatim.

### Operating requirements (standing project prompt)

- **Maximize P(Win; own the outcome:** prioritize defensible generalization, reliable automated checks, clear uncertainty and accountable end-to-end results. Do not claim an unverified win.
- **Lane/novelty:** run only the explicitly assigned method paragraph. Compare the candidate surface before placement and final dots after placement against all registry rasters. Reject if absolute rank correlation is over `0.90` or more than `70%` of candidate dots fall within `3 px` of any registry raster. Never copy a prior submission as a new candidate; prior files are for learning/audit only. Do not quietly exempt a raster.
- **Shared evaluation:** use the shared cached feature stack, `scripts/evaluate_holdout.py`, and `scripts/submission_writer.py`. Hold out whole fault segments with a buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, and evaluate pooled DTI with alpha `0.2`, beta `0.8`, and a `300 m` triangular kernel. Fix defects centrally, not in a private fork.
- **Leakage and scores:** test each feature alone; AUC over `0.90` is presumed leakage until resolved. Label measured results `HOLDOUT-DTI` with evaluator version, withheld-positive count and 95% CI; label a live result `ORGANIZER-CONFIRMED` only with its submission-page receipt; otherwise use `OWNER-REPORT`. A holdout or projection is never a live score.
- **Run card and budget:** each experiment records its hypothesis, mechanism, plausible named non-fault mimic, labeled holdout result and CI, registry correlation/overlap, raster SHA-256, validator output, submission name and note (<=140 characters), plus `promote` or `negative`. Stop after 3 experiments or 2 hours, whichever comes first. A positive experiment is not a weekly-slot selection; keep slot approval separate.
- **Submission gate:** exact saved GeoTIFF bytes must be single-band, finite and in `[0,1]` over the whole array, and match the organizer sample's CRS, shape and transform. Do not publish an upload CTA unless automated gates and separate promotion approval pass.
- **Research:** prefer scientifically grounded, free/official data. Distinguish official sources from mirrors and owner reports; state missing inputs, uncertainty, competing processes and limitations. This is a fault-propensity task, not direct proof of geothermal vents.

## Current executive decision

- [Executive summary and nine-site audit](docs/executive-summary.html) — table for GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36. Historical scores are explicitly marked owner-reported; a defensible live-score estimate is not available. Their submitted variants are compared against one another and flagged as overlapping/duplicate under the stated cohort gates.
- [Current candidate evidence](evidence/apart3_cthg_dhc_run_card.json) — H-APART3-2-CTHG-DHC; literal final-dot uniqueness fails and Band 6 total-count was misinterpreted as magnetic tilt. **Not OK to submit.** Diagnostic HOLDOUT-DTI in the card is not a leaderboard score.
- [This repository review](docs/repo-review-2026-10-28-session.md) — three-pass findings, changed files, verification and next actions.
- [Latest portal feed](docs/data/latest-run-card.json) — generated from the current negative CTHG evidence card. The root [`run_card.json`](run_card.json) and `docs/data/latest-run-card.json` historically diverged: the former is the fail-closed archival CSHD review; the latter has been synchronized to current CTHG status. See [repo review](docs/repo-review-2026-10-28.md).
- [Candidate research directions](docs/research/next-hypotheses-20261028.md) — three ranked hypotheses with mechanisms, mimics, cost and data caveats. They are unvalidated proposals, not assigned experiments.
- [How to submit, if a future candidate is authorized](docs/executive-summary.html#submission) — currently no candidate is authorized. Confirm contest identity/quota at the official portal before any future upload.

The current audit artifact [`apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif`](docs/downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif) is retained for scientific/reproducibility review only. It failed the literal all-registry overlap test and the science-integrity gate. **Its presence in the repo is not a recommendation to download or submit it.** The earlier withdrawn CSHD raster [`apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif`](docs/downloads/apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif) is likewise retained only as historical audit evidence, is not a submission recommendation, has SHA-256 `65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38`, and had historical name `APARTGEMSDOE3-CSHD-37B32D5B`.

## Known limitations and next actions

1. The parallel-run prompt refers to an assigned single-method paragraph, but none was supplied in this task text. Do not invent the lane.
2. The ignored `.cache` feature stack and full registry raster set are not in this checkout. The hash-pinned `sample_submission.tif` was restored from an owner-maintained GitHub mirror for local format testing; this is not organizer authentication. Training data is login-gated at the competition data page.
3. Correct and verify the shared Band 6 mapping, invalidate dependent cached features/models, then perform feature-level leakage canaries and (only once lane and budget are explicit) at most three controlled experiments / two hours.
4. Preserve literal pre-placement and final-dot comparisons. Do not ignore the dense 5-px calibration lattice or other raster solely to make a candidate pass.
5. Reconcile prompt leaderboard numbers against dated official receipts/snapshots. No live score estimate should be published without a validated calibration study.
6. Keep an executive feed generated from the same current release card, and require the automated validator plus separate weekly-slot selection before recommending a file.

## Reproduce checks

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json
.venv/bin/python scripts/check_release_status.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_submission.py \
  --template .cache/gems_data/sample_submission.tif --strict-finite \
  docs/downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif
```

Restore only retrieves hash-pinned mirrors; it does not grant organizer provenance or fill the full feature cache. `scripts/build_review_site.py` regenerates the fail-closed pages and latest status feed.

## Sources for review

- [Official competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN airborne magnetic/radiometric survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)
- [EPSG:32611](https://epsg.io/32611)

Links are supplied for source review; their live content/access was not independently refreshed in this repo review. Do not infer organizer confirmation from the mirrors or owner-maintained project sites.
