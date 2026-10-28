# Repository review — 2026-10-28

## Executive decision

**No file is approved to submit in this release.** The candidate most recently recorded in the checkout is `H-APART3-1-CFKC-DHC`, with a TIF under `docs/downloads/`. It must remain an audit artifact: the candidate's own uniqueness report records **99.8513%** of final dots within 3 pixels of a registered calibration-lattice raster, exceeding the literal protocol limit of 70%. The candidate report's exclusion of that raster from the ordinary "genuine discrete" maximum does not waive the protocol's “any registry raster” criterion. A research result is not a weekly-slot selector decision.

This review checks repository files, JSON consistency, file inventory and the applicable written protocol. No new scientific experiment or GeoTIFF was generated: the prompt refers to a single method paragraph but does not identify one, the full cached training stack is absent, and the existing candidates hit the literal duplicate stop. We therefore did not choose a new method lane or consume a competition slot.

## Findings (ordered by severity)

### P0 — Release artifacts contradict the duplicate-stop rule

- `evidence/apart3_cfkc_dhc_run_card.json` calls the candidate `promote` and `ok_to_submit: true`, while its own `correlation_and_overlap_vs_registry.literal_5px_calibration_lattice_probe` reports `within_3px_fraction: 0.998513` and the project protocol stops above `0.70`.
- That run card's ordinary max overlap (`0.656265`) is calculated on a subset of 465 genuine rasters. It excludes calibration probes, whereas the prompt says *any registry raster*. The separate calibration row is a direct counterexample and triggers stop.
- Older generated README/site copy promotes BHGC-3 and provides a green submit/download CTA. It conflicts with the later CFKC run card, the literal duplicate limit, and the independent selector requirement. Some of those legacy pages claim a live upload is ready; they must not be treated as current release decisions.
- Corrective action in this review: README and landing/executive pages now state `DO NOT SUBMIT`; the canonical root `run_card.json` records the negative decision and the exact reason. The raw historical run card is preserved as evidence, with its contradictory field noted rather than silently rewritten.

### P1 — Full pipeline cannot be independently reproduced in this checkout

- The competition labels and sample-submission grid were restored to ignored `.cache/gems_data/` from the hash-pinned owner mirror specified by `registry/ci_format_manifest.json`. Their hashes were verified, but the mirror is not organizer-authenticated. Training features and the full prepared stack remain absent.
- The initial Python environment did not have the project dependencies. They were installed into an ignored local `.venv`; the suite then ran with `88 passed, 2 skipped`. The skips require prepared competition data. Full holdout/evaluator rerun and prediction rebuild remain unavailable without training features.
- `scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite` was run on the existing CFKC and BHGC files. Both passed single-band float32, finite whole-array `[0,1]`, EPSG:32611, `3730 × 3292`, and transform checks against the owner mirror. This is not organizer validation, scientific validation, or release authorization.

### P1 — CI can validate format but cannot reproduce modeling

- CI now restores the minimum labels/template files from an integrity-pinned owner mirror and validates saved candidate TIFs against that template. The source is explicitly not organizer-authenticated; the check establishes local format compatibility only.
- CI does not restore the full training-feature stack or reproduce fold-local training/holdout metrics. A green format check must not be confused with a scientific or release pass. Preserve the data provenance label and fail clearly if either mirror hash changes.

### P1 — Site generator is stale and can recreate false release claims

- `scripts/build_site.py` reads root `run_card.json`, but its templates hard-code the earlier BHGC-3 filename and positive status and load BHGC experiment data. Before this review, the generated pages and root README also presented BHGC-3 as promoted. The newer CFKC run record was not the page generator's source of truth.
- This review adds a fail-closed guard that refuses to regenerate the old pages when the canonical card is negative or lacks separate slot authorization. The positive templates themselves remain legacy. Next, refactor the builder to consume one versioned release manifest, render current status without stale fields, and add a generated-site consistency test.

### P2 — Scores and scores-to-holdout mapping are not official receipts

- The nine historical score figures in the request/README are marked `OWNER-REPORT`, not organizer-confirmed. No receipt linking each exact raster hash to each reported score was found/verified in this review.
- The supplied `0.2778` GEMSDOE32 record is the highest reported score in the named nine-site subset. It is not evidence that a novel method will score higher. Holdout-DTI values measure local validation and are not a calibrated conversion to leaderboard score.
- The latest local CFKC record reports **HOLDOUT-DTI**, evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positives, `0.114452`, 95% CI `[0.100521, 0.128472]`; and **HOLDOUT-DTI**, evaluator `GEMSDOE32-SGMC-CAL-v3.0`, 62,703 withheld positives, prevalence-calibrated `0.081407`, CI `[0.073738, 0.088249]`. These are values transcribed from the historical run card, not rerun in this review and not organizer scores.

### P2 — Submission artifacts and naming conventions are confusing

- `docs/downloads/` contains multiple site-named, campaign-named, and historical TIFF/ZIP files. The visible landing page previously called more than one candidate "primary" and exposed direct download links without a current authorization gate.
- Keep audit artifacts, but make their state machine explicit: `research artifact`, `format-valid`, `duplicate-stop`, `selector-authorized`, and `organizer-scored` must not collapse into one green “validated” label. This review's candidate state is `research artifact` + `format-valid against owner mirror` + `duplicate-stop` + `not authorized`.

## Nine-site executive conclusion

The historical figures supplied for GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36 are summarized in `README.md`. The best reported score in that supplied set is GEMSDOE32 at **OWNER-REPORT 0.2778**. This number is not an estimate for the current candidate. Without the organizer's official receipts and a reproducible, correctly blocked local evaluator, a numerical leaderboard-score estimate would be speculative and is intentionally not given.

The prior `0.3195` and `0.4413` values in the user prompt conflict with repository's dated public leaderboard notes (which describe a 2026-10-26 observation of 0.4437). No claim about today's live leaderboard is made here; the leaderboard must be checked at the official URL immediately before any competition decision.

## What was checked in this review

- Confirmed the current branch and clean initial working tree before edits.
- Listed tracked data, source, scripts, tests, evidence, and downloadable raster artifacts.
- Inspected README, current-status/run-card records, CFKC and BHGC run cards, submission writer/checker, site builder, Pages workflow, and relevant tests.
- Compared the recorded literal calibration-lattice overlap against the user-specified stop threshold and corrected the release verdict to negative.
- Restored the pinned owner-mirror `labels.tif` and `sample_submission.tif` into ignored `.cache/gems_data/`, with exact SHA-256 checks. Provenance is owner mirror, not organizer authentication.
- Restored the pinned GEMSDOE24 calibration-lattice raster from its pinned GitHub commit and verified its SHA-256; compared both candidate TIFs against that one registry raster using `scripts/audit_release.py`.
- Independently measured directional 3-px overlap diagnostics (not scores): CFKC `0.9985127742`; BHGC `0.9974504701`. Both exceed the 0.70 protocol limit. This is a one-raster partial audit, not a full uniqueness scan.
- Ran `scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite` on both candidates; each passed the listed byte-format checks against the owner-mirror template. This does not authorize submission.
- Installed requirements in the ignored local `.venv` and ran `.venv/bin/python -m pytest -q`: **88 passed, 2 skipped**, with 32 Rasterio transform deprecation warnings after adding the independent recheck tests. The skips require the prepared feature cache.
- Ran `scripts/check_release_status.py`: passed the fail-closed status, candidate overlap threshold, slot-unused and metadata SHA-256 checks. It does not replace the format audit above or the missing full-registry scan.
- Ran the HTML parser over the landing/status/summary entry points and `git diff --check`; both completed without errors.
- Ran `scripts/build_site.py`; it refused to regenerate legacy positive pages because the canonical release card is negative. This is an intentional safety guard, not a successful full-site build.

## Deferred hypothesis shortlist (not experiments)

Four qualitatively ranked, untested geological research directions—with layers, mechanisms, distinctiveness checks, confounds, and cost rank—are recorded in [`docs/review.html`](review.html) and [`docs/review-2026-10-28.md`](review-2026-10-28.md). They are proposals only: the prompt does not identify the assigned lane paragraph, complete feature stack, or full comparison registry. Their novelty and data coverage have not been verified; no expected DTI improvement is asserted. Official sources for possible inputs are listed there, with access/coverage still to verify.

## Next actions (no slot until all are green)

1. Install the declared development dependencies and obtain the competition rasters through authorized access; record source, SHA-256, licensing/terms, and exact sample template provenance.
2. Keep the owner-mirror format check distinct from the official template. Re-run strict saved-byte validation against an organizer-authenticated template if/when authorized competition data becomes available; capture both source provenance and logs.
3. Fix the shared registry comparator to apply the literal protocol to all registered rasters, including calibration probes. Do not add an exemption without written protocol approval.
4. Add tests that reject a candidate with any `>70%` 3-px overlap, and tests that prevent any website or generator from presenting an unauthorized candidate as ready.
5. Re-run all 91 feature-only canaries and the spatially blocked hide-and-recover evaluator using visible-only catalogue-derived features, exact visible-trace masking, pooled DTI, and the specified uncertainty calculation. Audit whether the existing evaluator exactly implements the agreed 300 m triangular kernel and document its version/hash.
6. Update `scripts/build_site.py` and CI to consume a single release-status source and work safely without private competition data. Add an automated broken-link/asset/claim consistency check.
7. For research hypotheses: preregister one lane and at most three experiments/two hours; use cached feature stack; run surface and final-dot registry checks before release; do not spend a competition slot unless the candidate beats the current holdout best and the separate selector approves it.
8. Obtain organizer submission receipts before changing any score label to `ORGANIZER-CONFIRMED`; check the official leaderboard live rather than using cached values.

## Source links for manual review

- [DrivenData GEMS overview / rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData submission/data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [DrivenData reference solution (official organization GitHub)](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN airborne survey page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project information](https://gbcge.org/current-projects/ingenious/)
- [DOE/NLR GEMS technical report](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
