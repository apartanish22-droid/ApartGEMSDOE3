# ApartGEMSDOE3 — research and submission review

> **DO NOT SUBMIT: no candidate has cleared the required gates.** No new experiment or competition slot was used in this review. The historical CSHD promotion is withdrawn: its recorded final-dot overlap exceeds the literal all-registry limit and it inherits a scientifically misidentified feature. Format validity is not submission authorization.

The standing project prompt and operating protocol are summarized in [the project charter](docs/PROJECT_CHARTER.md); read it before every session. The full repeated prompt was not preserved verbatim in this repository; the charter is not a substitute for reading current user instructions.

[Executive summary and nine-site audit](docs/executive-summary.html) · [Review and limitations](docs/repo-review-2026-10-28.md) · [New research proposals](docs/research/next-hypotheses-20261028.md) · [Current run card](run_card.json)

The historic artifact [apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif](docs/downloads/apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif) (SHA-256 `65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38`; historical name `APARTGEMSDOE3-CSHD-37B32D5B`) is **for audit only**. It passes local format/range checks against an owner-mirrored sample, not organizer-authenticated data. Its historical holdout values are not verified leaderboard predictions. Its original promotion card is archived under `evidence/cshd_historical_promotion_card_20261028.json`.

The checkout does not include the cached feature stack or full registry raster set. The supplied protocol refers to a lane paragraph that is absent, and the literal overlap gate also flags a space-filling calibration grid. These are blockers to a compliant new raster, not reasons to silently relax the gate. Band 6 was treated as magnetic tilt in BHGC and CTHG although previous forensic evidence identifies radiometric total count; cached derivatives and dependent results require rebuilding after source metadata is verified. Competing prompt leaderboard claims are not independently confirmed. Site scores are owner reports, not organizer-confirmed receipts.

## Reproduce checks

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group core --manifest registry/ci_format_manifest.json
.venv/bin/python scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite submission/apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif
.venv/bin/python scripts/check_release_status.py
.venv/bin/python -m pytest -q
```

Restored samples are hash-pinned third-party mirrors, not organizer-authenticated. `scripts/build_review_site.py` builds the fail-closed portal; old portal builders are disabled because they could republish an invalid promotion claim. Research download links are not a submission recommendation.

Official starting points: [competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), and [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). Access and current content were not independently verified in this sandbox.
