# ApartGEMSDOE3 — submission research

> **DO NOT SUBMIT:** No new submission has passed the complete parallel-run protocol in this session. Existing TIFFs are for research only. Format validation alone is not upload authorization. See the [executive summary](docs/index.html) and [review and run card](docs/review-2026-10-28.md).

## Project brief and working principles

The goal is to develop an independently generated, competitive geothermal fault-prediction GeoTIFF with an automated and auditable research-to-submission workflow. Maximize the probability of success and own the outcome, including negative results. Prefer verified official sources, distinguish user/owner-reported values from organizer receipts, and never treat projected scores as measured scores. No high score can be guaranteed.

Start each session by reading this README, the current review, and the user's full parallel-run instructions. Required controls: stay within the **assigned single method lane**; reuse the shared feature stack, holdout evaluator and writer; hide whole fault segments and rebuild catalogue features using visible faults only; test individual features for leakage; check surface rank correlation and final-dot overlap against **every** registry raster; validate finite `[0,1]` values and exact organizer grid; label holdout statistics with evaluator, withheld count and CI; stop at the experiment/time budget; leave slot promotion to a separate selector. Incomplete evidence means no promotion. The prompt in this session did not specify the lane.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

Many integration tests require data that is not committed. The CI format manifest fetches only two hash-pinned **owner-mirror** files, not an authenticated competition dataset. `scripts/restore_data.py` can restore further manifest items where permitted. For strict file validation:

```bash
.venv/bin/python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json
.venv/bin/python scripts/check_submission.py --strict-finite docs/downloads/apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif
```

A pass only compares with the owner mirror; it does not certify scientific validity, uniqueness, competition acceptance, or permission to spend a slot. Competition information: [DrivenData](https://www.drivendata.org/competitions/306/competition-doe-gems/) and [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution). Older site pages and evidence contain historical claims and are not current release decisions.
