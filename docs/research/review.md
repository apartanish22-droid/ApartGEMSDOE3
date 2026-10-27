# Research and reproducibility review — 27 October 2026

## Decision

**No new TIFF is cleared or available for competition submission.** The supplied
parallel-run protocol refers to a “single method paragraph below,” but this prompt
contains no paragraph assigning a particular method to this session. Choosing a
lane ourselves could collide with parallel work. There is no authenticated complete
registry of all concurrent/private runs, no cached derived template stack in this
checkout, and no same-protocol frozen incumbent here. No geological experiment or
weekly submission was attempted in this review. A concurrently merged parallel run did
create an MRCJ research TIFF; its previous “promote” claim is superseded by the
independent [lattice audit](../../evidence/mrcj_audit.json), and the
[run card](../data/run_card.json) distinguishes source-reported from independently
measured evidence.

### Parallel MRCJ: a concrete duplicate-stop

A separate run on main published `apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif`
with SHA-256 `fb4400e342e8aab8b059e067cfac8b2225b48534e46800d6efe69c2f2d9403d1`.
We reopened those exact bytes: 37,654 positive in-footprint pixels, none outside;
all 37,654 are within three pixels of the registered calibration lattice
(**100.00%**, limit **70%**). The nine historical file overlaps range from
22.61% to 27.39%, illustrating why the earlier nine-only screen was incomplete.
The saved file passes local all-finite range and grid checks relative to the
hash-pinned owner mirror, not an organizer acceptance check. The independent
final-dot binary Spearman with the lattice is approximately 0.00006246; this is
not a pre-placement surface correlation, which is unavailable. One failed
reference suffices to stop; the complete registry was not scanned.

The parallel run reports **HOLDOUT-DTI 0.022070** (evaluator
`gems-segment-pooled-v1`, 60,988 withheld positives, 95% spatial-block CI
[0.017237, 0.026923]), but this review did not replay its scientific analysis.
Its comparator is explicitly described as a static H33 map rather than a
fold-rebuilt, promotion-grade incumbent. The earlier run auto-selected a method
despite the missing assigned lane and claimed a slot promotion; neither satisfies
the supplied protocol. Its artifact and original run card are preserved for
research; the corrected card is negative and the old runner now fails closed
before writing. [Original run card](../../evidence/mrcj_original_run_card.json)
contains historical claims, not current authority. **Do not submit the TIFF.**

### What the independent byte audit establishes

The [reproducible audit](../../evidence/prior_audit.json) fetched the exact nine named
historical reference files and one lattice witness at immutable Git commits. SHA-256
pins verify those mirror bytes, not their official origin or any organizer score.
Comparisons use every positive footprint pixel, the shared template's Euclidean
3-pixel halo, and exact binary Spearman on the common footprint. They do not cover
all registry entries, unavailable rasters, or pre-placement score surfaces.

- All 72 directed comparisons among these nine files exceed the protocol's 70% overlap limit with at least one another; in fact, each of the 72 crosses it. They are therefore not unique to one another under this rule, even if filenames or file hashes differ.
- The GEMSDOE25 and GEMSDOE30 historical **positive support** is identical. The GEMSDOE32 H33-B2 support is exactly the GEMSDOE25 support after removal of points at distance ≤2 pixels from the mirrored known-fault catalogue. It is a subset of the GEMSDOE31 support; the latter has 2,545 extra dots. The GEMSDOE36 historical raster contains the H33 support plus 1,200 dots. These are geometry measurements, not scores.
- The registered spacing-five lattice has 206,895 positive pixels; 5,160,724 of 5,167,373 footprint pixels are within 3 pixels, leaving 6,649 uncovered. For any raster with **N distinct in-footprint dots**, at least `max(0, N − 6,649)/N` overlap it. At the commonly used N=37,654, the minimum is 82.34%, already above 70%. This is a geometry lower bound for this budget, not a proof that every smaller raster is impossible. Lowering the budget or steering dots into boundary holes merely to game the test is not evidence of discovery. A policy decision about the literal registry definition is needed; we do not exempt the lattice ourselves.
- The two-pixel collar is a method choice, **not** an organizer scoring exclusion. [DrivenData staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2) say known-fault *pixels* are masked in both rounds. The impact of excluding their neighborhood depends on the hidden fault geometry and is unknown.

## What can be said about the reported GEMSDOE32 value?

The prompt reports **0.2778 USER-REPORTED / UNVERIFIED** for H33-B2; it is the
largest supplied number among the nine historical claims. The current GEMSDOE32
page says its file-to-score receipt is absent, and an older audit manifest calls
the candidate unscored. That does **not** prove whether a later upload happened;
it does mean this checkout cannot establish a file-bound organizer score. Do not
present the value as ORGANIZER-CONFIRMED, a holdout result, or a projection.
[Original manifest at pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/1398109a23f04a2ace71c1bd2f527cfba87860b5/docs/downloads/submissions_manifest.json)
· [Current site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html).

One plausible explanation *if* the score report is correct is that sparse dot
placement and pruning of low-utility predictions reduced weighted false-positive
mass or overlap redundancy. This is a hypothesis, not causation: hidden labels,
public/private masks, and the receipt linking this exact file to its result are
unavailable. Removing near-catalogue points could also discard useful new faults.
No honest numerical probability or projected leaderboard score follows from the
available evidence. A new model could surpass the report, but this run did not
validate a candidate that does so.

### The metric, without an invalid simplification

The [official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)
defines `TPw` as the sum of the *best* weighted prediction for each truth pixel,
`FPw` as a sum over predicted pixels weighted by their distance to truth, and
`FNw = |G| − TPw`. With binary dot count `N`, `T = TPw` and `M` the sum over dots
of their own best truth-kernel weights, the denominator is

`D = 0.2 * (T + N − M) + 0.8 * |G| + ε`.

In general `T ≠ M`; therefore replacing the denominator with `0.2*N + 0.8*|G|`
is unjustified. One dot can give nonzero credit to several truth pixels, so its
marginal truth credit may exceed its own maximum truth-kernel weight. That error
appears in the **prose**, not necessarily the arithmetic, of the pinned shared
metric and was reported in [issue 50](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50).
The [staff aggregation clarification](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550/2)
says leaderboard components are pooled over the public subset before the index is calculated.

## Data and tooling audit

| Asset or source | What was actually checked | Limitation |
| --- | --- | --- |
| [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Public fetch redirects to login. | We do not have competition login or private truth; no credentials were requested or stored. |
| [Pinned owner-mirror manifest](../../registry/input_manifest.json) | Core 19-band TIFF was restored from five pinned parts; each part and assembled bytes match published hashes. Labels, sample, historical rasters, lattice, and a derived four-band radiometric mirror were also hash-verified. Grid metadata matches across the named inputs. | A hash establishes identity with a third-party mirror, **not** official origin, license permission, or data quality. This review's downloads are in ignored `.cache/`; the parallel branch separately committed some mirror TIFFs. |
| Alleged sample | The mirrored sample has 60,988 positive cells, identical to the mirrored catalogue's positive support. | The official problem page describes an all-fault-absence sample, so this discrepancy prevents authenticating it as the real sample. It is used as a provisional grid/footprint only. |
| [Shared 57GEMSDOE template](https://github.com/buffedlizard55-lab/57GEMSDOE) | The locally restored files match pinned upstream Git blob IDs and SHA-256 hashes. | The upstream repository had no license file or GitHub license metadata when checked; independent permission for reuse and redistribution was not established, so source files are not republished here. |
| [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Official page describes airborne magnetics/radiometrics and their public data release, CC0. | The derivative quantization and provenance of the owner mirror were not independently reproduced from USGS files. |
| [GDR INGENIOUS](https://gdr.openei.org/submissions/1391) | Public page lists temperature probes and many other resources and CC BY 4.0. | Specific probe bytes, local coverage, and competition compatibility have not been tested here. |
| [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) | USGS describes elevation products free and without use restrictions. | Coverage and input downloads for the research hypotheses were not verified here. |
| [USGS NHD](https://www.usgs.gov/national-hydrography/national-hydrography-dataset) | USGS says downloads remain available. | The NHD was retired in 2023 and is no longer maintained; 3DHP is the current program. Exact local coverage is unverified. |

The source input raster uses a very large negative nodata sentinel. It must not be
passed through as a prediction. The [shared writer at the pinned commit](https://github.com/buffedlizard55-lab/57GEMSDOE/blob/822a0ce5546c7b6749cdd82eb145b6b3e616603d/src/gems57/submission_writer.py)
rejects nonfinite/out-of-range predictions rather than silently clipping; the
[local checker](../../scripts/validate_submission.py) reopens bytes and checks
band count, CRS, shape, transform and ranges. Its extra all-finite/zero-outside
policy is stricter than the footprint checks and is **not** an organizer acceptance
receipt. The problem page says data outside bounds is null/NaN; whether zero
outside the irregular survey footprint will be accepted is not established.
The user's portal error cannot be attributed to any particular nodata mode without
the rejected file and response details.

### Shared-tool irregularities

- [GEMSDOE32 issue 49](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/49): the shared 32-channel builder's bright-ridge helper selects the smaller-absolute Hessian eigenvalue despite describing the largest. A synthetic Gaussian stripe verified suppression; this is not a model score. The cache must not be trusted as described until fixed upstream. We do not maintain a local corrected fork.
- [Issue 50](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50): shared metric prose incorrectly bounds `dT` by a dot's self-credit; reported with a counterexample. The 57GEMSDOE integration denied issue creation, so it was reported to the repository vendoring the template.
- Existing [issue 37](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37): GEMSDOE32's CLI wrappers silently binarize probabilities. The separately pinned `gems57` writer/evaluator preserve probabilities; do not use the affected wrappers as a general soft-score pipeline.
- Existing [issue 41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41): that repository's holdout implementation may omit false positives in zero-truth cells. It is not safe to promote results that depend on the affected case without the upstream fix.
- Existing [issue 42](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42): that repository's surface-stage check can ignore overlapping preview dots. Use the literal shared gate and stop on either threshold.

## Next work, in order

1. Obtain the omitted single-method lane and reconcile the literal lattice/continuous-surface registry scope across the parallel group; do not silently change the rule.
2. Authenticate competition inputs and licensing against the official download, and locate the actual shared derived cache or obtain the upstream ridge fix before use. Check actual quota and official encoding at the portal.
3. Freeze a complete accessible registry, a same-protocol incumbent, seeds and a spatially blocked whole-segment split. Run feature-only canaries before the top assigned hypothesis. Compare a fold-local model with the incumbent on pooled DTI and paired spatial-block CIs.
4. Check both pre-placement and final-dot novelty against the complete inventory, save/validate the exact TIFF and note, then let a separate selector decide whether it deserves a weekly slot. No human image inspection is a required gate; local automation still cannot certify private truth or portal acceptance.

A geological fault indication is not proof of an active geothermal vent or a
commercial resource. Field/organizer verification is separate from automated
submission readiness.
