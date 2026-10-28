# Repository review — 2026-10-28

## Decision
**Negative; DO NOT SUBMIT.** The existing CSHD raster passes the strict format validator but fails the literal registry overlap gate. This session generated no new TIF and used no competition slots. The stop-on-duplicate protocol takes precedence over the request to keep iterating. No assigned single method paragraph was present, so no new lane was invented.

## Three passes
1. Read README, runners, shared release gates, manifests, evidence, CI and tests. Restored hash-pinned template and labels from GitHub mirrors. Initial suite: 96 passed, 2 skipped. Found that the checker required promotion while explicitly requiring a failed literal all-raster gate.
2. Restored the hash-pinned calibration lattice and independently ran `audit_release.py` on current CSHD bytes. Directional overlap is 0.9975832580867903, above 0.70. All strict format checks pass. This measurement is geometry, NOT a score. Corrected canonical verdict, made site generation fail closed, and made the runner stop on literal gates instead of density-filtered gates. Preserved pre-review run card as historical evidence.
3. Added regressions rejecting the previous inconsistent promotion, re-ran suite (98 passed, 2 skipped; 33 dependency deprecation warnings) and status checker, and rebuilt the portal. No fresh hide-and-recover training or new hypotheses were tested after the duplicate stop.

## Ranked research backlog — proposals, not validated discoveries
These are conditional proposals for a later explicitly assigned lane. Ranking is qualitative expected utility, not a projected DTI. No claim of global novelty is made; repository coverage cannot establish what other parallel sessions have implemented.

| Rank | Hypothesis and layers | Signature and missing-fault rationale | Difference / cost / mimic |
|---|---|---|---|
| 1 | Cross-spectral contact displacement: cached GeoDAWN magnetics and radiometric K/Th | Compare displacement of magnetic gradient ridges with radiometric contact edges at multiple scales; buried edges lacking a surface radiometric contact may indicate concealed structure | Explicit cross-layer offset rather than the existing CSHD dual-cover envelope. Medium cost. Mimic: buried volcanic contact. Availability of cached input bytes must be restored and band identities verified before viability is asserted. |
| 2 | Curved-front segmentation: cached elevation and basement depth | Along-front curvature change points corroborated by basement gradient, targeting discontinuities beneath piedmont sediment | Change-point statistic rather than generic scarp strength or tip extension. Medium cost. Mimic: alluvial-fan incision. Not validated; inspect existing transforms for exact overlap before assigning lane. |
| 3 | Radiometric attenuation boundary: K, Th, U and elevation | Co-located attenuation of all radioelements with a narrow, persistent magnetic edge; potentially sediment-covered fault contact | Attenuation consistency rather than alteration-ratio anomaly. Low-to-medium cost. Mimic: soil moisture and survey seam. Not viable until cached band descriptions and coverage are verified. |

No new external source is proposed as already obtainable. Official source for GeoDAWN provenance: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and . Network policy blocks direct verification of USGS here; GitHub mirrors are not official authentication. Do not turn these hypotheses into submission recommendations without data provenance, per-feature canaries, spatially matched comparisons against the current best, and literal registry checks.

## What the evidence does and does not establish
The historical CSHD HOLDOUT-DTI, evaluator GEMSDOE32-HIDE-RECOVER-v3.0, is 0.109189 with 95% CI [0.097298, 0.120981], n=22,232 withheld positive pixels. This is copied from historical run evidence, not rerun, not ORGANIZER-CONFIRMED, and not a projection of leaderboard performance. The static/collared evaluation differences in prior evidence also mean cross-method numbers are not automatically comparable.

The reported GEMSDOE32 result and the conflicting leaderboard highs in the user prompt lack organizer receipts in this session. Official reference repository was reachable through GitHub API; direct DrivenData, USGS, NLR, and Dropbox access is outside this sandbox's allowed hosts. Source links are provided for provenance and future checking, not represented as fetched/verified pages.

## Next steps and limitations
- The lattice is space-filling: overlap alone does not demonstrate scientific copying. Nevertheless the requested literal rule forbids exemption. A policy change requires an explicit protocol revision; the project must not silently relax it.
- Do not rerun `run_cshd_pipeline.py` expecting a promotable artifact under the present registry; it now stops on the literal failure.
- No validated unique **new** submission was produced. Do not rename, perturb, or copy the existing raster to claim uniqueness.
- Only this repository's Pages content was changed. External GEMSDOE24–36 websites were not edited.
- Obtain organizer receipts and a current submission-cap observation through a permitted authenticated workflow before any separate selector decision. No credentials should be committed.
- Restore cached feature stack and competition inputs before any next training run. Format mirrors prove byte consistency, not organizer authentication. No GPU or data-download guarantee is made.
- Persist a single assigned method paragraph and preregister a matched holdout experiment before the next budget cycle.

Official reference: https://github.com/drivendataorg/gems-prize-reference-solution
Competition rules/problem: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
