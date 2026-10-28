# ApartGEMSDOE3 project charter

This charter is the durable starting point for project work. It captures the user's standing objectives and parallel-run constraints without repeating duplicate prompt text. Read it before changing the modeling or release pipeline.

## Outcome and values

- Build an auditable, useful research portal for DOE GEMS geothermal-fault propensity mapping, with official sources and an obvious submission/release decision.
- Maximize the probability of a defensible competition result; own the outcome end to end. Never turn a local metric into a leaderboard claim.
- Develop scientifically distinct, plausible hypotheses using free/official data when possible. State missing data, uncertainty, caveats, and competing processes explicitly.
- Provide a download CTA only when an artifact is both validated and explicitly authorized. A structurally valid GeoTIFF can still be scientifically poor, duplicate, or unauthorized.

## Required experiment protocol

1. **Method lane / duplicate guard:** define one method lane per run. Before placement and again on final dots, compare the surface rank correlation and dot overlap against every applicable registry raster. Stop if absolute rank correlation exceeds `0.90` or more than `70%` of candidate dots fall within `3 px` of a registry raster. Apply the literal registry rule; do not exempt calibration or synthetic rasters unless the protocol is formally changed and recorded.
2. **Shared tools:** use the shared cached feature stack, `scripts/evaluate_holdout.py` and `scripts/submission_writer.py`. Fix shared-tool defects centrally, not in a private method fork. Hold out whole fault segments with a buffer; derive catalogue features only from visible faults; mask visible faults pixel-exactly; evaluate pooled DTI with alpha `0.2`, beta `0.8`, and the `300 m` triangular kernel.
3. **Label every score:** identify each numeric result as `HOLDOUT-DTI` with evaluator version, withheld-positive count and 95% CI, or `ORGANIZER-CONFIRMED` only when copied from an organizer submission receipt. Owner-reported values must be called `OWNER-REPORT`. A projection is never a score.
4. **Leakage canaries:** test each feature alone on the holdout. AUC above `0.90` is presumed leakage until resolved.
5. **Run card:** each experiment ends in a JSON card with hypothesis, mechanism, plausible non-fault mimic, holdout DTI and CI, registry comparisons, raster SHA-256, validator output, submission name/note (note <= 140 characters), and `promote` or `negative` verdict.
6. **Budget/selection:** max three experiments or two hours, whichever comes first. Do not consume a competition slot for an unvalidated idea. A positive experiment result is not a submission authorization; weekly-slot selection is a separate step.
7. **Submission format:** single-band GeoTIFF matching the official sample's CRS, shape and affine transform; all predicted values finite and in `[0,1]` across the whole array, including outside the footprint. Validate the exact saved bytes automatically.

## Repository operating rules

- Review `README.md`, this charter, `registry/current_status.json`, and the current candidate card named there before modeling work. `run_card.json` is an older fail-closed CSHD archive; do not treat it as the latest candidate card.
- Maintain an auditable source register and distinguish official sources from owner-provided repositories, score claims, and local model outputs.
- Never copy a prior submission as a candidate. Prior rasters can be used for audit/education only.
- The README and site landing page must state whether an artifact is actually OK to submit and give clear reasons when not.
- Avoid making up leaderboard score estimates. Report measured holdout DTI instead and explain that it is a proxy, not a conversion to live score.
