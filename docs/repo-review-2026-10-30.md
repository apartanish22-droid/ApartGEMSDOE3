# Repository review — 2026-10-30

## Executive decision

**DO NOT SUBMIT any artifact from this checkout.** No new TIF was created and no weekly slot was used. The current site and registry correctly fail closed. Creating a TIF simply to satisfy a download request would contradict the required lane, holdout, leakage, uniqueness, and selector gates.

## Pass 1 — inventory and source-of-truth review

- Read the persistent project brief in `README.md`, `registry/current_status.json`, `docs/executive-summary.html`, the nine-site audit, and the latest candidate/run-card records.
- The README's current decision is DO NOT SUBMIT. It identifies the latest candidate as negative and explains that scores supplied by the owner are not organizer receipts.
- The nine-site files audit is `evidence/nine_site_best_files_audit.json`. It describes artifact bytes and score labels as `OWNER_REPORT`; it is not evidence that an artifact is eligible or that the stated score is an organizer-confirmed result.
- The best historical score supplied for GEMSDOE32 is 0.2778 (OWNER-REPORT). Its why/how cannot be causally established from leaderboard values alone. Pruning/placement differences may be hypotheses, not proof. No legitimate leaderboard score estimate for a new candidate is supported by this review.

## Pass 2 — operational and scientific gate checks

- The assigned method paragraph is absent from the checkout; a lane cannot be inferred safely.
- The full training-feature raster and cached feature stack are not available in this checkout, so a compliant holdout, feature-alone leakage canary, and new candidate surface cannot be run here.
- Existing research artifacts have known release blockers, including overlap with the literal 5-pixel calibration lattice. This must not be waved away as an exception: the protocol says compare against every registry raster.
- The source/template provenance for prior format checks is an owner mirror, not an authenticated organizer template. Format pass alone is not submission authorization.
- No candidate meets every scientific, uniqueness, format, and separate selector gate. Do not surface a TIF as “OK to submit.”

## Pass 3 — verification performed this session

- `python3 scripts/check_release_status.py` → **PASS**: current and historical candidates fail closed; hashes match; portal is current; no slot used.
- `python3 -m compileall -q src scripts tests` → **PASS**.
- `python3 -m pytest -q` → **NOT RUN**: this interpreter has no `pytest` installed (`No module named pytest`). This is an environment limitation, not a passing test result.
- Working tree was clean before this review. No experiment was run; do not count this review as one of the method experiments.

## Nine-site executive ranking (reported historical scores only)

| Site | Highest score stated in supplied record | Confidence label | Release choice now |
|---|---:|---|---|
| GEMSDOE24 | 0.2477 | OWNER-REPORT | None authorized |
| GEMSDOE25 | 0.2600 | OWNER-REPORT | None authorized |
| GEMSDOE27 | 0.2449 | OWNER-REPORT | None authorized |
| GEMSDOE28 | 0.2710 | OWNER-REPORT | None authorized |
| GEMSDOE30 | 0.2600 | OWNER-REPORT | None authorized |
| GEMSDOE31 | 0.2708 | OWNER-REPORT | None authorized |
| GEMSDOE32 | 0.2778 | OWNER-REPORT | None authorized |
| GEMSDOE33 | 0.2632 | OWNER-REPORT | None authorized |
| GEMSDOE36 | 0.2750 | OWNER-REPORT | None authorized |

These are the best scores stated in the supplied prompt, not a freshly verified leaderboard snapshot. The current comparative file audit should be consulted before interpreting file-level differences. “Highest supplied value” is not the same as an approved file to download or submit. Estimated score for any new candidate: **not estimable**.

## Three new-session candidate hypotheses

The repository already holds a four-item qualitative shortlist at `docs/research/next-hypotheses-review-20261028.md`. Its leading proposal—buried basement-step ridge with surface-quiescence gate using in-competition depth-to-basement/elevation layers—is a test priority only, not a fresh session lane. The next session should select a single assigned lane before running any experiment and first perform candidate-vs-incumbent feature-level novelty checks. No new external data source is required for that proposal, but the data/cache bytes are currently unavailable. Alternative shortlist ideas are directional semivariogram anisotropy and signed cross-edge magnetic–gravity offset; both are adjacent to prior methods and require detailed code-level overlap review before treating them as novel.

## Highest-priority blockers and follow-up

1. Restore verified organizer competition data and the cached stack using the documented restore/data process; record exact provenance and hashes. The current CI mirror is not organizer authentication.
2. Resolve the missing assigned lane paragraph and register one experiment with its stopping rule before executing anything.
3. Re-run the prescribed leakage canaries and whole-segment buffered hide-and-recover via shared evaluator/writer only; compare against same-evaluator incumbent and report spatial 95% CI.
4. Audit the literal registry, including the calibration lattice, before placement and on final dots. Any threshold breach means stop/negative.
5. Install the declared development dependencies in a venv and run full tests. Repair any shared evaluator/writer defect centrally.
6. Keep the selector separate. A promising holdout is not an organizer score, projection, or authorization to spend the weekly submission allowance.

## Official review pointers

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/)

Links are source pointers, not assertions of live reachability during this review.

## Run card (review-only; no experiment)

```json
{
  "hypothesis": "No experiment: assigned lane missing and required cached feature stack unavailable.",
  "mechanism": "N/A — review only; no raster generation or feature fitting occurred.",
  "named_non_fault_mimic": "N/A — no candidate surface was evaluated.",
  "holdout_dti": "NOT RUN; no evaluator result or confidence interval claimed.",
  "correlation_overlap_vs_registry": "NOT RUN this session; previous audited artifacts have literal calibration-lattice overlap failures.",
  "raster_sha256": null,
  "validator_output": "No new TIF. Existing fail-closed release-status check passed; no claim of organizer-template validation.",
  "submission_name": null,
  "submission_note": "Review only; no candidate or slot authorization.",
  "verdict": "negative"
}
```
