# Repository review — 2026-10-30

## Decision

**DO NOT SUBMIT any file in this checkout.** No file has passed the release gate, the uniqueness gate, or the selector step. This review ran no new experiment and used no weekly slot.

## Checks run (all reproducible)

| Check | Command | Result |
|---|---|---|
| Restore pinned format inputs (owner mirror, not organizer-authenticated) | `python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json` | Verified 2 files (`labels.tif`, `sample_submission.tif`) |
| Test suite | `python -m pytest -q` | **109 passed, 2 skipped** (before restore: 107 passed, 2 failed for missing `.cache/gems_data/sample_submission.tif`) |
| Release gate | `python scripts/check_release_status.py` | PASS — fails closed; hashes match; no slot used |
| Format validator on every shipped TIF | `python scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite <file>` | See table below |
| Official leaderboard | `fetch_page` on the DrivenData leaderboard URL | Read 2026-10-30 (see Finding 2) |
| Official submissions page | `fetch_page` on the DrivenData submissions URL | Redirects to login (path confirmed under competition `306`) |

### Format validator results (shipped TIFs)

- **PASS (format only):** every `zeros` variant in `docs/downloads/` and `submission/`, including the CSHD, CTHG, CFKC, BHGC, WCHD, and unique-offcatalogue candidates, and the GEMSDOE32 0.2778 file (`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`).
- **FAIL:** every `nan` variant. Validator detail: `whole-array range [nan, nan], finite=False`. **This is the most likely cause of the "Predicted values must be in range [0, 1]" error** if a `nan` file was the one uploaded. We could not confirm which file was uploaded.
- A PASS here means only "shape, CRS, transform, and value range are valid." It is not scientific, uniqueness, or submission authorization.

## Findings

### 1. No file is cleared to submit (blocking)

`registry/current_status.json` sets `any_file_ok_to_submit: false`. The gate requires all of the following, and none is met:

- An assigned method lane. **The lane paragraph referenced in the parallel-run protocol is not present in the prompt or the repo.** Without it, no lane can be assigned.
- Feature-alone leakage canaries at or below 0.90 AUC. Not computed here.
- A fold-local HOLDOUT-DTI win with a paired 95% CI above 0 against the current same-evaluator best. Not run.
- Literal uniqueness against every registry raster (Spearman ≤ 0.90 and ≤ 70% of dots within 3 px). **Fails.** `registry/registry_uniqueness_scan_20261028.json` reports `literal_all_rasters_final_passed: false`. Its worst overlap is GEMSDOE23 (69.6% within 3 px, 91,533 other dots). Its worst surface is GEMSDOE22 (surface Spearman 0.238, within-3 px 80.0%, 335,879 other dots). Focus-site and genuine-surface checks pass, but the literal all-raster check does not.
- Separate weekly-slot selector approval. Not present.

**Conclusion:** the fail-closed state is correct. Nothing in this checkout should be downloaded or submitted as a new candidate.

### 2. Leaderboard figures in the prompt and repo are stale (irregularity — flagged for review)

Official leaderboard, read 2026-10-30 via `fetch_page`: [drivendata.org/competitions/306/competition-doe-gems/leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

| Rank | Participant | Best public DW-Tversky |
|---|---|---|
| #1 | xiaofanhu | **0.4544** |
| #2 | cfld__ | 0.3916 |
| #3 | Batik Shirt Brothers | 0.3911 |
| #4 | BrandenKMurray | 0.3841 |
| #5 | op01 | 0.3642 |

- The prompt's **0.4413** matches the 2026-10-25 snapshot. The repo's 2026-10-26 snapshot shows 0.4437. Today's official page shows **0.4544**.
- The prompt's **0.3195** is an early-October value. In the 2026-10-04 snapshot in `registry/leaderboard_history.jsonl`, DARD was #2 at 0.3195 and nchuzhoy was #1 at 0.3262. It is **not** the current high and should not be used as the target. The current top is 0.4544.
- Today's observation has been appended to `registry/leaderboard_history.jsonl` (date only; time of day was not captured).
- `docs/data/feed.json` and `scripts/build_site.py` still carry the older "current top" text in places. This needs a separate feed-update pass; this review did not rewrite those narratives.

### 3. Wrong competition ID in links (fixed)

Several links pointed to `drivendata.org/competitions/309/competition-us-doe-gems/...`. The official competition is **306**, `competition-doe-gems`. Fixed in `scripts/build_site.py` and `docs/research/pre-review-readme-20261028.md`. No `309` links remain in the repo's docs. `build_site.py` and `build_review_site.py` were rerun and produced no further output change.

### 4. Estimated score for any new file

Not estimable. There is no organizer receipt linking any file hash to a score. The 0.2778 for GEMSDOE32 is an `OWNER-REPORT`. HOLDOUT-DTI numbers are diagnostics only and are not converted to leaderboard projections (for example, the current candidate's HOLDOUT-DTI is 0.002126 [0.001567, 0.002606], n=22,232).

### 5. Housekeeping

- Four separate `docs/repo-review-*-2026-10-28*.md` files and several `docs/research/*review*` files overlap heavily. Recommend consolidating into one dated review per session, with older ones moved to an archive folder.
- The `.cache/` inputs are gitignored and must be restored in each fresh checkout (`scripts/restore_data.py`). CI does this already (`.github/workflows/pages.yml`).
- Rasterio emits 33 `PendingDeprecationWarning`s for `Affine *` multiplication (`rasterio/transform.py`). Switching to `@` is a low-risk cleanup.

## What is missing before any new candidate can be generated

1. **The assigned method lane paragraph** (the protocol cannot run without it).
2. **The cached feature stack** (≈419 MB, not restored; see `docs/repo-review-current-session-2026-10-28.md`).
3. **A complete registry** of rasters for the literal all-raster uniqueness check (current scan covers 784 unique SHA-256 entries, not verified against the live registry).
4. **An organizer-authenticated template.** The format inputs are owner mirrors. DrivenData login is required for the data page (`https://www.drivendata.org/competitions/306/competition-doe-gems/data/`), and the login redirect was confirmed.

## Suggested next steps (ranked by P(Win) impact per unit of effort)

1. Supply the lane paragraph and confirm the 2-hour / 3-experiment budget.
2. Restore the feature stack from a reproducible owner source and re-verify its hashes.
3. Compute single-feature leakage canaries before any model work.
4. Run the literal all-raster uniqueness check on the surface before placement and on final dots.
5. Only after those pass, consider the one weekly slot through the separate selector step.
6. Update `docs/data/feed.json` so the "current top" language reflects the 2026-10-30 leaderboard (0.4544).

## Sources checked in this review

- Leaderboard (official): https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Submissions page (login-gated, path check only): https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/
- Data page (login-gated): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Local evidence: `registry/current_status.json`, `registry/registry_uniqueness_scan_20261028.json`, `registry/leaderboard_history.jsonl`, `data/restore_receipt.json`.
