# ApartGEMSDOE3 — autonomous submission research

> **DO NOT SUBMIT: current CSHD artifact fails the literal all-registry uniqueness gate.**
> Automated strict format validation passes; it is not submission authorization.

[Executive summary and research-only TIF download](docs/executive-summary.html) · [Three-pass review and ranked hypotheses](docs/research/session-review-20261028.md) · [Current run card](run_card.json) · [Independent byte recheck](evidence/session_literal_review_20261028.json)

## Starting point for every session
Read this charter, current run card and review before working. Own the outcome: prefer measured negative findings over unsupported high-score promises. Maximize P(Win) through reproducible evidence and no wasted submission slots.

This session independently restored the pinned template and calibration lattice. Current CSHD dots overlap that raster within 3 px by **99.758326%**, exceeding the literal **70%** gate. No density exemption is authorized. The previous ready-to-submit claim is superseded. No new TIF, experiment or live slot was used after this finding. A new scientific candidate cannot be honestly certified under these conditions.

Research-only artifact: [`apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif`](docs/downloads/apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif).

The current file is finite, single-band float32 in [0,1], EPSG:32611, shape (3730,3292), and exact template transform. Its SHA-256 is `65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38`. Name: `APARTGEMSDOE3-CSHD-37B32D5B`. These are artifact metadata, not a score.

Historical HOLDOUT-DTI: **0.109189**, CI **[0.097298,0.120981]**, evaluator **GEMSDOE32-HIDE-RECOVER-v3.0**, **22,232 withheld positives**. Not rerun this session; not an estimate of leaderboard performance. Owner-reported results for the nine sites are listed separately on the executive page and are not organizer-confirmed. No live estimate is available.

## Reproduce review
```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_release_status.py
.venv/bin/pytest -q
```
The pinned lattice source is in `registry/data_manifest.json`; exact recheck results are in `evidence/session_literal_review_20261028.json`. The portal is published via the existing GitHub Pages workflow after tests pass. Historical README claims are retained in [the superseded snapshot](docs/research/pre-review-readme-20261028.md), not current recommendations.

## Concurrent review preserved
The main-branch review also flags Band 6 total count being interpreted as magnetic tilt in inherited features (`IR-CTHG-BAND6-TC-02`). See [its scientific review](docs/repo-review-2026-10-28.md) and [additional hypothesis backlog](docs/research/next-hypotheses-20261028.md). Verify semantics and invalidate dependent caches before further training. This session did not repair that scientific mapping.

## Limitations and next work
No uniquely assigned method paragraph was supplied. Direct DrivenData/USGS/Dropbox access is restricted in this environment. Pinned GitHub mirrors are not organizer authentication. No current leaderboard, organizer score receipt or weekly cap was verified. Only this site's executive summary can be updated here, not the other owners' websites. Stop-on-duplicate prevents further generation in this run. See the review for three ranked conditional research hypotheses and next-session prerequisites.

## Standing request (normalized charter from earlier sessions)
The expanded repeated user request is summarized below rather than misrepresented as a verbatim transcript. Priority: unique valid TIF; literal lane gates; honest score labeling; no live slots without separate selection; three-pass review; PR and merge. A negative result is a deliverable.

## Standing Parallel-Run Protocol Charter

<details>
<summary>Click to view the normalized project prompt & Parallel-Run Protocol instructions</summary>

```text
Please put this prompt into the repo README.md, complete any pending work, and keep working on the next steps autonomously.
Download the required data from the official competition (https://www.dropbox.com/scl/fo/6335d42764f2a6663c883/AI6-f_2a2s3d4f5g6h7j8k9l0?rlkey=y7z8x9c0v1b2n3m4q5w6e7r8t&dl=1), and prepare the data for our training and inference pipeline automatically.

Review the repo and focus on the highest score from the list below:
GEMSDOE24: 0.2477
GEMSDOE25: 0.2600
GEMSDOE27: 0.2449
GEMSDOE28: 0.2710
GEMSDOE30: 0.2600
GEMSDOE31: 0.2708
GEMSDOE32: 0.2778
GEMSDOE33: 0.2632
GEMSDOE36: 0.2750

We need an executive summary and a table to show for each site, what is the best submission file to download, what is the estimated score and if it's a unique submission unlike any other GEMSDOE sites.
We also MUST generate a unique .tif submission for the competition. Do not copy a previous submission (only download for learning or comparison, not for submission). It should be obvious if the generated .tif is validated and ok to download and submit, or not.
All inspection and validation can be done automatically in the project without a human inspector.
Also study GEMSDOE32's h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778 deeply at a PhD level why and how it gets 0.2778 and if/how we can beat 0.2778.
How did the top of the leaderboard get 0.3195 (0.4413)? Can we beat 0.3195?

Before implementing anything, propose 3–5 untried candidate geological hypotheses for hidden faults and geothermal vents/conduits:
- Exact layers used
- Physical signature / transform
- Why it catches faults missing from the USGS/INGENIOUS catalogue
- How it differs from existing repo implementations
- Rank by expected DTI improvement vs. implementation cost.

PARALLEL-RUN PROTOCOL — follow strictly:
1. LANE. Implement ONLY the geological method described in your assigned paragraph below. Do not add other methods. Before and after dot placement, check uniqueness against the submission registry: if rank-correlation with any registry raster > 0.90 OR > 70% of your dots fall within 3 px of a registry raster's dots, STOP and log as duplicate. Check on the surface before placement and on final dots.
2. REUSE. Do not rewrite the evaluator, validator, or data loader. Import from the template: evaluate_holdout.py, submission_writer.py, and the cached feature stack. Holdout = hide-and-recover whole fault segments with buffer, catalogue features derived only from visible faults, visible faults masked pixel-exactly, scored with pooled distance-weighted Tversky (alpha=0.2, beta=0.8, 300 m triangular kernel). If you find a bug in a shared tool, fix it in the template and note the commit — never keep a private fork.
3. LABEL EVERY NUMBER. Every figure you report must be tagged either HOLDOUT-DTI (with evaluator version, number of withheld positives, and 95% CI) or ORGANIZER-CONFIRMED. Never write a projection as a score.
4. LEAKAGE CANARY. Test each feature alone on holdout first; AUC > 0.90 means leakage until proven otherwise.
5. OUTPUT. End with one JSON Run Card: {hypothesis, mechanism, named non-fault mimic process, holdout DTI + CI, correlation/overlap vs registry, raster sha256, validator output (single-band, finite, in [0,1], CRS/shape/transform match), submission name + <=140-char note, verdict: promote | negative}.
6. BUDGET. Stop after at most 3 experiments or 2 hours. Do not submit to the live leaderboard — a separate selector picks at most 2 winners across all parallel runs.

Predicted values must be in range [0, 1].
Execute in 3 passes (Pass 1: implement & verify; Pass 2: review & fix bugs/edge cases; Pass 3: re-check against all requirements), then create and merge a PR onto main.
```

</details>
