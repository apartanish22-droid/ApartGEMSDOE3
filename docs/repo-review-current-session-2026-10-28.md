# Repository review — current session, 2026-10-28

## Decision

**NEGATIVE — DO NOT SUBMIT any file in this checkout.** This review ran no experiment, generated no TIF, and used no weekly slot. Upstream main now contains a separately generated research artifact and run card; this review reassessed that record without rerunning it. The assigned method lane paragraph, large feature stack, and complete registry remain absent, so the required canaries and full uniqueness gates cannot be reproduced here. We did not relax those requirements or authorize a download.

This session is on `arena/e7422e50-apartgemsdoe3`. Existing run cards were not rewritten as if their old experiments occurred on this branch. The current session's no-experiment JSON card is [`evidence/session_review_20261028.json`](../evidence/session_review_20261028.json).

## Checks run and results

1. Read `README.md`, `docs/PROJECT_CHARTER.md`, existing `run_card.json`, current status registry, nine-site audit, release pages, research notes, and shared holdout/writer interfaces before deciding whether to run anything.
2. Initial tests could not start because the system Python did not have pytest or NumPy, and system-wide pip installation was blocked by PEP 668. Created ignored `.venv/` and installed the declared `requirements.txt` dependencies from PyPI.
3. First test run: **96 passed, 2 skipped, 2 failed** because the ignored local `.cache/gems_data/sample_submission.tif` and `labels.tif` inputs were missing. Restored only the hash-pinned sample, label, and existing-fault files from the owner-mirror manifest (combined about 2.4 MB); reverted the tracked restore receipt after the test-only restore. These are owner mirrors, not organizer-authenticated inputs.
4. Final test run after merging current status/evidence: **107 passed, 2 skipped** (`.venv/bin/python -m pytest -q`). It emitted 33 Rasterio `PendingDeprecationWarning`s about affine multiplication; no functional test failure remained.
5. Ran `scripts/check_release_status.py`: **PASS**, negative/closed release state, historical raster hash matches, no slot used.
6. Ran `scripts/check_submission.py --strict-finite` on the historical CSHD TIF against the restored sample mirror: **format PASS** — one-band float32, EPSG:32611, shape 3730×3292, transform match, whole-array finite and within `[0,1]`. This is only a structural-format result; it does not authorize submission.
7. No model, leakage-canary, holdout, pre-placement registry, or final-dot experiment was run in this review. The imported candidate card has a separate historical HOLDOUT-DTI diagnostic; its full-registry comparison is explicitly not run. The required feature stack and full raster set are not present locally. We did not use a leaderboard score projection.

## Findings / irregularities to resolve

- **Lane paragraph absent:** no method can be selected without inventing an assignment. This is an explicit protocol blocker.
- **Current candidate and inherited experiment:** the latest recorded artifact on merged upstream main is `H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS`, with SHA-256 `8d90342de3a9d62bb718ea209ed5644cca0878eff906029dbc975da438cdcafd`, documented in `evidence/H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS_run_card.json`. This review did not rerun it. Its card reports HOLDOUT-DTI 0.002126 [0.001567, 0.002606], evaluator `GEMSDOE32-HOLDOUT-v3-visible-gated`, n=22,232; it is a weak diagnostic, not a leaderboard projection. Feature-alone canaries were not computed and the full registry comparison was not run. The current-status/feed/site pointers now identify it as the current negative candidate. CTHG-DHC and root CSHD remain separate negative historical candidates.
- **Unique is not verified:** the imported card says off-catalogue by construction, but does not compare its surface or final dots against every registry raster. That is not a uniqueness pass; the candidate remains negative and no download link or selector action is authorized.
- **Stale branch provenance:** root `run_card.json` names `arena/4d26cf27-apartgemsdoe3` and an earlier review card names another branch. These are historical experiment records from other session branches, not current-session provenance. Preserve them as history and use this review card for this branch.
- **Nine-site evidence class:** the values in the executive summary are copied from user/repository claims, not organizer submission receipts. The page correctly says `OWNER-REPORT`; there is no valid estimate for a new submission. Of the supplied nine, GEMSDOE32's 0.2778 is the highest reported value. The available evidence is consistent with a nested “prune near-catalogue dots” family, but does not establish that pruning caused the live score or predict a better score. See [`knowledge/03_why_02778_and_the_anatomy_of_the_family.md`](../knowledge/03_why_02778_and_the_anatomy_of_the_family.md).
- **Historical artifacts fail release criteria:** the root card's archived CSHD results report a failed literal all-registry uniqueness gate (including about 99.76% within 3 px of a registered calibration lattice); its scientific interpretation also inherits a band-mapping issue. CTHG-DHC has separately documented uniqueness and scientific-integrity failures. Neither is a submit candidate.
- **Site build regression identified and fixed:** the original `scripts/build_review_site.py` wrote identical executive-summary HTML to the landing page and every named subpage. It now creates distinct pages with consistent navigation and fail-closed status, and `tests/test_review_site_builder.py` guards against identical pages and broken/Markdown-style links. Pages were regenerated after the fix.
- **No live feed verification:** Pages at GitHub Pages, DrivenData, USGS, and other sources were not fetched in this session; network egress is restricted to GitHub/code hosting and package registries. Links in repository source registers remain review pointers, not newly verified source contents.
- **Cached input gap:** this test-only restoration did not download the approximately 419 MB feature raster or external derivatives. It cannot unlock a compliant holdout; training or feature generation was not attempted.

## Research shortlist and next steps

A ranked shortlist of four unrun, bounded candidates is in [`docs/research/next-hypotheses-review-20261028.md`](research/next-hypotheses-review-20261028.md). The first priority is a scale-persistent sediment-cover step ridge with an explicit surface-quiescence gate, using the feature-stack bands already described in the repository. It is a qualitative research priority, not a predicted score or an authorized lane. No test was run because the assigned lane, predictor stack, and complete registry are missing.

Before another experiment: (1) assign the missing method paragraph and record a fresh two-hour/three-experiment budget; (2) restore/hash-check organizer data if available, the feature stack, cached stack, and complete registry; (3) reconcile band semantics, evaluator/writer version, and status feed; (4) canary each feature independently; (5) execute visible-only buffered segment holdout with exact masking and pooled DTI; and (6) run literal all-registry uniqueness before and after placement. Only a separately authorized selector may consider spending a weekly slot.

## End-of-review run card

The machine-readable card in [`evidence/session_review_20261028.json`](../evidence/session_review_20261028.json) records a negative no-experiment result, null holdout metric, the audit-only historical artifact hash, the format check, and no download/submit authorization.
