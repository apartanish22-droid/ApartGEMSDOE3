# GEMSDOE32 H33-B2: forensic interpretation and score provenance

## Bottom line

The prompt identifies `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` as the top result among the nine specified GEMSDOE sites. The public owner-side focus-nine audit records that value as **OWNER-REPORTED** and states that no authenticated submission-page receipt is archived for it. Therefore this repo cannot certify that the raster bytes here were uploaded, that the organizer assigned that exact value to those bytes, or that the reported result is a causal effect of the named method.

The strongest supported explanation is **metric-efficient pruning of an existing spatial field**, not proof of a new physical discovery: removing redundant/low-credit prediction mass can improve a distance-weighted Tversky ratio if it preserves coverage of withheld faults. The reported H33-B2 file is part of a nested sparse family; the owner audit reports substantial overlap with the other focus-site masks. It is not a unique submission under the stated rule.

**Freshness caveat:** this describes the pinned historical focus-nine artifact audit, not the newest output in every participant repository. An owner-maintained [GitHub freshness receipt](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/a73f9ffba29260cc7708e8e0557c84c5bea7d47b/docs/data/portfolio_freshness.json) reports all nine repository `main` refs differed from its exact-file audit refs at its recorded check time, and explicitly says new-head TIFFs/scores were not audited. Latest method records for GEMSDOE30 POOL-1 and GEMSDOE36 TCD-36 are separately summarized in the repo review; they are research/holdout records, not receipts for historical competition scores.

## Evidence and limitations

The references below are owner-maintained research artifacts, not organizer receipts:

- [GEMSDOE36 focus-nine source-integrity audit, pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/focus9-source-integrity.json)
- [GEMSDOE36 pairwise uniqueness report, pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/7edcc9b58e6ad0f88c6e6f5ee9218761a391769d/docs/downloads/focus-sites-pairwise-uniqueness.json)
- [GEMSDOE30 explanation note, pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/d21ddd9502f3c3911e8d77b8f1e6abfaadffc876/docs/research/2026-10-25-lsm/why-h33-scored-0.2778.md)
- [GEMSDOE32 repository](https://github.com/buffedlizard55-lab/GEMSDOE32)

What those records report:

- H33-B2's historical score is **0.2778 OWNER-REPORTED** (not ORGANIZER-CONFIRMED).
- The owner audit records a positive-pixel count of `37,654` for the H33-B2 mask. The same owner-side audit reports that it is nested within the D2.8/solo family and that every one of the nine named top masks fails the stated focus-nine uniqueness rule.
- The same audit reports the GEMSDOE25 and GEMSDOE30 D2.8 masks have zero pixel-set XOR, the H33-B2 mask is a strict subset of that family, and the GEMSDOE36 historical mask adds points over H33-B2. These are byte/mask comparisons in an owner-published audit, not independent calculations in this checkout.
- The owner analysis describes the H33-B2 recipe as a thin/pruned H19-5-derived field with an exclusion near the visible-fault catalogue. That history is plausible context, but its feature lineage and fold-locality have not been re-run here.

The listed historical sequence is recorded only as owner-reported claims:

| Historical arm | Reported value and provenance | Interpretation, not causal proof |
|---|---|---|
| H19-5 parent field | `0.1922` — OWNER-REPORTED; no receipt in the cited audit | Dense parent surface in the reported lineage. |
| D2.8 thinning | `0.2600` — OWNER-REPORTED; no receipt in the cited audit | A sparse subset reportedly retained enough kernel coverage while reducing prediction mass. GEMSDOE25 and GEMSDOE30 are reported to share the same positive mask. |
| Solo/B1 pruning | `0.2708` — OWNER-REPORTED; no receipt in the cited audit | The reported method removes a narrow near-catalogue collar; that can suppress halo predictions around known traces, but only fold-local construction is valid in holdout. |
| H33-B2 | `0.2778` — OWNER-REPORTED; no receipt in the cited audit | The reported top among the nine; still fails novelty. |
| Andersonian PINN extension | `0.2750` — OWNER-REPORTED; no receipt in the cited audit | The owner audit describes extra dots beyond H33-B2 and a lower reported value, consistent with low marginal value of added mass. |

These values are **not HOLDOUT-DTI** because no evaluator version, withheld-positive count, and confidence interval accompany them. They are also **not ORGANIZER-CONFIRMED** because the cited sources do not archive submission-page receipts. They must not be presented as a validated estimate for a new candidate.

## Why sparsification can help under the official metric

The official [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) specifies a triangular distance kernel with `300 m` support and a distance-weighted Tversky index using `alpha=0.2` and `beta=0.8`:

\[
\mathrm{DTI}=\frac{\mathrm{TP}_w}{\mathrm{TP}_w+0.2\,\mathrm{FP}_w+0.8\,\mathrm{FN}_w+\epsilon}.
\]

The implication is about **marginal spatial coverage**, not simply “fewer dots is always better.” Weighted true-positive credit is determined by nearby maximum prediction contributions; once nearby pixels already cover the same hidden-truth neighborhood, another correlated pixel may contribute little extra `TP_w`. A pixel that is not close to a hidden positive can still add weighted false-positive mass. Thus thinning a broad ribbon or excluding a low-quality collar can improve the ratio if it removes mostly redundant/low-credit pixels and retains the important 300 m coverage. Conversely, over-thinning can sharply increase false negatives because `beta` is larger than `alpha`.

This is a scientifically plausible *metric mechanism*. It does not establish that H33-B2's withheld test faults were covered better, that the “B2” exclusion was built without leakage, or that the score belongs to the exact archived bytes. The GEMS task itself emphasizes incomplete public fault data and expert-labeled hidden faults; fitting only visible catalog geometry is not evidence of finding the hidden set.

## Could this project beat the reported value?

**No validated answer is available.** The merged checkout has a mirrored sample/grid, known-fault masks, evaluator code and a prior MRCJ research artifact, but not the authenticated full competition feature stack or complete current registry. A prior MRCJ HOLDOUT-DTI is recorded with evaluator, withheld-positive count and 95% CI; it was not replayed in this review and is not calibrated to organizer scores. No new holdout or leakage-canary experiment ran in this review. Consequently there is no new HOLDOUT-DTI, no new confidence interval, and no basis for a numeric prediction. The project must not claim “higher than H33” until a new method beats a comparable shared-evaluator holdout baseline and passes registry/format gates in an authorized future cycle.

For context only, the [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) fetched on **2026-10-27** displayed a top public entry of `0.4544` (**ORGANIZER-PUBLIC-LEADERBOARD snapshot; not a submission-page receipt and not a score estimate for this project**). The leaderboard is dynamic and reports public-test standings; it is not a final/private prize result. The prompt's `0.4413` and `0.3195` “current” values are older/conflicting user-reported figures relative to that fetched snapshot.

## Submission decision

- **Do not download or submit** any of the nine historical top TIFFs; the owner-side comparison says they all fail the focus-nine uniqueness threshold.
- The H33-B2 value is for learning and metric analysis only. No copied or renamed file was generated.
- No slot was used. Promotion to a real upload is a separate selector decision and must not be inferred from this analysis.
- The prior MRCJ artifact's only safe status is **research-only / negative / not ready**. The current selector returns `DO_NOT_SUBMIT`; the official format, full-registry and paired-current-best gates are not satisfied. Future work requires authorized inputs and a fresh, fully gated review.
