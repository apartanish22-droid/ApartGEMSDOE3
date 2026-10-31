# Session review — 2026-10-31

**Verdict: DO NOT DOWNLOAD OR SUBMIT ANY FILE FROM THIS SESSION.** No candidate has cleared the uniqueness gate, the organizer-authenticated template check, or a holdout win. Nothing in this session is a leaderboard estimate.

Machine-readable record: [`evidence/session_20261031_run_card.json`](../../evidence/session_20261031_run_card.json).

## 1. Why this session did not produce a "submit now" TIF

The request asked for a unique TIF that is obviously safe to download and submit. The repo's release gates cannot be cleared in this sandbox:

| Gate | Status | Why |
|---|---|---|
| Organizer-authenticated template | **Blocked** | DrivenData data page requires login. The template used here is a SHA-256-pinned owner mirror on GitHub, not an organizer file. |
| Uniqueness (Spearman ≤ 0.90 and ≤ 70% dots within 3 px vs every registry raster) | **Not run** | The full registry is not restored in this checkout. Only the nine focus files were compared. |
| Holdout win vs compliant incumbent | **Not attempted** | No new candidate was built. Building one within this session's budget was not justified (see §5). |
| Scientific / selector authorization | **Not granted** | The repo protocol keeps promotion separate from the weekly slot selector. |

A file that passes the format check alone is not a competition submission. The repo has several such files, and all are marked negative.

## 2. Why GEMSDOE32 scored 0.2778 (answer)

Source: [`knowledge/03_why_02778_and_the_anatomy_of_the_family.md`](../../knowledge/03_why_02778_and_the_anatomy_of_the_family.md). The 0.2778 figure is **OWNER-REPORT**. No organizer receipt ties it to these bytes.

- **Metric.** `DTI = TP / (TP + 0.2·FP + 0.8·FN)`, with a 300 m triangular kernel. Each predicted pixel is scored by kernel credit. False-positive mass costs 0.2 per unit, and missed truth costs 0.8 per unit.
- **Family lineage (owner-reported).** The file is the B=2 variant of a nested family: H19-5 (121,131 dots, 0.1922), d2.8 (44,090, 0.2600), solo/B=1 (40,199, 0.2708), champion/B=2 (37,654, 0.2778). Each step removes dots.
- **Most plausible mechanism.** Pruning low-credit dots lowers FP mass faster than it lowers TP. Under the metric this raises DTI. The repo's archived overlap records say the B=2 variant excludes 2,545 dots within 2 px of the training catalogue.
- **Limit of the explanation.** The hidden truth and organizer receipts are not in the repo. So the repo cannot prove that B=2 caused the 0.2778 result, cannot infer per-dot credit, and cannot predict a new file's score.
- **Holdout check this session.** The shared evaluator reproduces the recorded incumbent value exactly: pooled HOLDOUT-DTI **0.0045154** (evaluator GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 withheld positives, 95% CI [0.003816, 0.005262]). See [`evidence/holdout_incumbent_recheck_20261031.json`](../../evidence/holdout_incumbent_recheck_20261031.json).
- **SGMC-calibrated proxy (not organizer labels).** Prevalence-calibrated DTI **0.0641** (GEMSDOE32-SGMC-CAL-v3.0, 62,703 withheld positives, 95% CI [0.056730, 0.071649]). Per [knowledge/10](../../knowledge/10_calibration_finding_and_next_candidates_20261030.md), this proxy is the one that correlates with live owner scores (ρ = +0.40, n = 117), while the hide-and-recover metric does not (ρ = +0.17, CI spans 0).

## 3. Verification log (this session, from bytes)

| Check | Command | Result |
|---|---|---|
| Dependencies | `pip install -r requirements.txt` in `.venv` | OK |
| Core format inputs | `scripts/restore_data.py --group core` | 2 files restored, SHA-256 verified |
| Full inputs | `scripts/restore_data.py --group all` | 36 files verified against `registry/data_manifest.json` |
| Tests | `pytest -q` | 119 passed, 2 skipped |
| Format check, GEMSDOE32 file | `check_submission.py --strict-finite` | PASSED (float32, whole-array [0,1], all finite) |
| Nine-site re-verification | `scripts/verify_nine_site.py` | Strict-finite PASS: GEMSDOE30, 32, 33, 36. **Fail (NaN present): GEMSDOE24, 25, 27, 28, 31.** Exact duplicate pair: **GEMSDOE25 = GEMSDOE30**. Output in [`evidence/nine_site_verification_20261030.json`](../../evidence/nine_site_verification_20261030.json). |
| Holdout reproduction | `scripts/evaluate_holdout.py` on the GEMSDOE32 file | Matches recorded value exactly |

## 4. Irregularities flagged for review

1. **Leaderboard conflict.** The brief cites 0.4413 as the GEMSDOE high and 0.3195 as the current high. The README records a 2026-10-30 public read of 0.4544 for #1. DrivenData was unreachable this session (HTTP 000), so no leaderboard value was re-read on 2026-10-31. **Do not use any of these values as a current reference without re-checking the live page.**
2. **Portal error vs. NaN files.** The user's portal error was "Predicted values must be in range [0, 1]". Five focus files contain NaN, and the README says NaN outside the footprint is allowed by the official page. **That official page could not be re-read here.** It is a plausible cause of the rejection, not a verified one. Treat the five NaN-containing files (GEMSDOE24, 25, 27, 28, 31) as unsafe until the official format text is confirmed.
3. **Duplicate.** GEMSDOE25 and GEMSDOE30 are byte-different but identical by rank and by positive mask.
4. **Owner pages not reachable.** The `buffedlizard55-lab.github.io` pages and `drivendata.org` are not in this sandbox's allowlist. The file list in the prompt was not re-verified from the pages. Only the GitHub-hosted mirrors were checked.
5. **Missing lane.** The parallel-run protocol refers to an assigned method paragraph. It is not in this checkout, so no lane was applied.
6. **Request vs. protocol.** The request asks for a unique file that is obviously safe to submit. The repo's protocol (README, Standing requirements item 7) allows a download CTA only after scientific, uniqueness, and selector gates pass. These do not both hold in this session, so the repo follows the protocol.

## 5. What was not done, and why

- **No new candidate was generated.** The repo already has many negative candidates. The shared holdout metric does not predict live scores well (ρ = +0.17). A holdout win would not justify a leaderboard estimate, and this session's budget was not enough for a full registry uniqueness check.
- **No score estimate.** No projection is written. Every number above is HOLDOUT-DTI, labeled with evaluator version, withheld count, and CI. The 0.2778 and other site scores are OWNER-REPORT.

## 6. Limits and what is needed

- **Organizer data.** A DrivenData account with the competition data page, to download the authentic template, labels, and sample submission. This is the single biggest blocker. Public owner mirrors are not organizer-authenticated.
- **Full registry.** All registry rasters, to run the uniqueness check (Spearman and 3 px overlap) properly. The current check covers only the nine focus files.
- **Official text.** A re-read of the submission-format PDF (<https://docs.nlr.gov/docs/fy26osti/96647.pdf>) to confirm how NaN and outside-footprint values are treated.
- **Live leaderboard.** A fresh read of <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> from a machine that can reach it.

## 7. Suggested next steps (ranked)

1. Obtain the organizer template. Without it, no file can be called submission-ready.
2. Re-read the official submission PDF and confirm the NaN rule. If NaN is rejected, regenerate the four NaN files with zeros outside the footprint and re-run `check_submission.py --strict-finite`. Do not submit them as-is.
3. Restore the full registry and run the uniqueness check against all rasters.
4. Adopt the SGMC-calibrated off-catalogue DTI as a secondary gate (V1 in knowledge/10). This is an owner decision.
5. Only then run one pre-registered experiment within the 3-experiment and 2-hour budget.

## Sources (official, for manual review)

- [Competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Submission format PDF (NLR)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [EPSG:32611](https://epsg.io/32611)
