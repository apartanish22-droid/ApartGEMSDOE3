# Three implementation / review / fix passes — 27 October 2026

These were software/evidence checks, not geological experiments. No TIFF in the
synthetic tests was a competition candidate; all were created in temporary test
directories and removed by pytest. The checked-in run remains negative.

## 1. Exact bytes, format and metric

Reviewed the independent geometry arithmetic and the template's exact scoring
and format helpers. Fixed our CLI so NaN or infinite *metadata* is represented
as a descriptive JSON string rather than causing `allow_nan=False` to crash;
the failed validation remains failed and no file pixels are repaired. Added
tiny-TIFF tests for incorrect range, nonfinite values, nodata, sentinel,
footprint/catalogue mass, CRS, transform, dtype, band count and hash mismatch;
checked binary Spearman against SciPy, Euclidean directed overlap, the lattice
bound, and shared metric terms against a brute-force transcription. Result:
**28 tests passed** at the end of this pass. The disputed metric prose was
reported upstream and not privately patched.

## 2. Feeds and site integrity

Reviewed feed parsing and discovered that the first parser could combine a
recognized header from one table with a rank-one row in a different table. It
now identifies the public score column and rank inside the same single table,
rejects ambiguous markup, and retains the last dated observation on failure.
Partial source-head errors keep their prior timestamps, and the UI no longer
claims all heads were checked at the same time. Completed the explanatory
pages, added site-specific source summaries and format diagnostics, and added
local link/anchor, generated-file and negative-status tests. Result: **45 tests
passed** at the end of this pass. The direct sandbox leaderboard request failed;
the earlier public-tool observation and its original time were preserved.

## 3. Shared-tool provenance, evaluation, and release

Added synthetic tests for the shared evaluator's pixel-exact visible mask,
zero-truth false-positive block pooling, paired block terms and buffered
whole-component hiding, plus writer rejection/ZIP round-trip. A fresh rerun of
the full historical audit matched the committed record except its timestamp;
the historical GEMSDOE32 file passed the *local* format diagnostic but remained
explicitly ineligible for a slot. Reviewed upstream licensing and found no
license metadata/file: replaced redistribution of the 24 shared files with a
hash-verified local restoration step, and added tamper/missing/unindexed-file
tests. Added CI and a scheduled static-site deployment design, and checked the
preview's pages, links and JavaScript. Result: **57 tests passed** after this
pass. Deployment capability and current source-host status must still be
verified separately; a passing test or Pages deploy is not scientific approval.
