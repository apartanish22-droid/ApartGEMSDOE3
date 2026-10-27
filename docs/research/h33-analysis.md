# Why the reported GEMSDOE32 result might be strong

## Evidence, not a claim of a verified score

The user and peer sites associate H33-2-B2 with **0.2778 USER-REPORTED / UNVERIFIED**. No submission-page receipt in this checkout links that number to the TIFF's SHA-256. It is the largest value in the nine historical claims supplied in the request, not a new prediction or a guarantee. The [organizer public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed a public leader at **0.4544, organizer leaderboard snapshot**, when viewed on 2026-10-27 around 21:20 UTC. It has no established relationship to our artifact. The conflicting 0.3195 and 0.4413 values in the brief cannot both be treated as the current top score.

## Independently replayed geometry

[`evidence/historical_audit.json`](../../evidence/historical_audit.json) records pinned Git blob identity, SHA-256 and exact raster operations. All geometry is relative to the same **peer-mirrored, not organizer-authenticated** footprint and label grid:

- The 44,090-dot GEMSDOE25 D2.8 and GEMSDOE30 D28 artifacts have exactly the same positive pixels within that footprint, despite different TIFF bytes.
- The H33 37,654-dot raster is exactly D2.8 after deleting the 6,436 dots whose Euclidean distance from the mirrored known-fault catalogue is at most two 100 m pixels. H33 adds no dots to that base.
- H33 is also a subset of the selected GEMSDOE31 historical raster; it removes 2,545 of those dots. The GEMSDOE36 historical raster contains every H33 dot and adds 1,200 others.
- These are geometry checks only. They do not establish hidden true positives, an actual organizer result, geothermal permeability, or the mechanism by which any score changed.

## Mechanism and limits

The [official metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) applies a 300 m triangular kernel and pools the resulting weighted true positives (T), false positives (F) and false negatives, with alpha = 0.2 and beta = 0.8. Organizer staff say known-fault pixels are [masked](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) and public pixels are [pooled](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550).

Sparsifying correlated predictions can plausibly reduce false-positive mass without losing all nearby true-positive credit, because the true-positive term uses the maximum nearby weighted prediction. A catalogue collar can remove redundant mass, but catalogue distance alone does not reveal whether a removed dot was informative. Let N be total truth mass and suppose a removal changes weighted TP and FP by nonnegative amounts t and f. Ignoring the tiny numerical epsilon, a removal raises DTI only when `0.2*T*f > t*(0.2*F + 0.8*N)`. We do not know T, F, N, t or f for the private or public hidden truth. Therefore the claimed ranking is **consistent with**, not proof of, improved efficiency. It is not a justified forecast.

## Could a distinct method do better?

Yes in principle: the public leaderboard contains higher values, but that is not evidence that our proposed method will reach them. A genuine improvement requires a new reproducible geological signal, correct fold-local validation against a comparable best, complete uniqueness checks, and the independent slot selector. Candidate hypotheses and confounders are in [the pre-registration](preregistration.md). None was executed here: the prompt lacks the referenced single method assignment and the necessary stack, comparable baseline and complete live registry are absent. The mathematical lattice constraint also blocks the familiar high-dot-count regime under the literal rule; see [the forensic audit](../../evidence/historical_audit.json). No automatic loophole or selective removal of the calibration control was used.
