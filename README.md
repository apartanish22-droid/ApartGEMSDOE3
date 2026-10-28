# ApartGEMSDOE3 — DOE GEMS fault-prediction research

> ## Current decision: **RESEARCH DOWNLOAD ONLY — DO NOT SUBMIT**
>
> **Research GeoTIFF:** [`docs/downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif`](docs/downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif)
> **SHA-256:** `9d5cab2ed8b393cd509c196961481520772bee5b1791e322e0b15cdbba696112`
> **Submission name / note (for a future selector review):** `APARTGEMSDOE3-CTHG-DHC-5D4D0085` / `ApartGEMSDOE3 H-APART3-2 CTHG-DHC 37654d B2 d3.24 | HR=0.0997 Det=0.0960 SGMC=0.0824`
> **Format validation:** passes the local owner-mirror template checks: one-band float32, `EPSG:32611`, `3730 × 3292`, exact transform, finite values in `[0,1]`, no NaNs, 37,654 positive pixels. This is **format validation, not upload authorization**.
> **Literal uniqueness gate:** **FAIL**. The final dots overlap a registered dense raster by **75.90%** and another by **72.25%**, both over the protocol's 70% limit. A registered 5-px calibration lattice has 99.80% overlap. The prompt provides no density or lattice exemption. The continuous surface passes its correlation threshold (`max |Spearman| = 0.212714`).
> **Scientific integrity gate:** **FAIL**. `IR-CTHG-BAND6-TC-02`: the implementation used Band 6 (`tc`, previously identified in this repository as radiometric Total Count) as magnetic tilt. The candidate's claimed tilt geology is not validly tested.
> **Selector / submission slot:** not run; no slot used. `ok_to_submit` is false. The file is retained for research and audit only.

The canonical machine-readable status is [`run_card.json`](run_card.json); detailed audit is in [`evidence/apart3_cthg_dhc_registry_uniqueness.json`](evidence/apart3_cthg_dhc_registry_uniqueness.json) and [`evidence/apart3_cthg_dhc_run_card.json`](evidence/apart3_cthg_dhc_run_card.json). The current site starts at [`docs/index.html`](docs/index.html), with a dedicated [executive summary](docs/executive-summary.html).

## What was tested

We recorded a research plan and ran three named pipeline arms for `H-APART3-2 (CTHG-DHC)`, reusing cached feature stacks, the local hide-and-recover evaluator, and submission writer. This was not a valid prospective preregistration: exploratory sweeps informed the final plan, and the cumulative experiment/time budget was not reconciled. More importantly, a post-run audit found `IR-CTHG-BAND6-TC-02`: the claimed magnetic tilt input is Band 6 (`tc`), while the repository's own earlier forensic work identifies Band 6 as airborne radiometric Total Count, not magnetic tilt. The physical interpretation is invalid until the shared feature builder and dependent caches are corrected. The stored results describe the flawed implementation and are retained as a negative research result. The full ledger is [`evidence/apart3_cthg_dhc_experiments.json`](evidence/apart3_cthg_dhc_experiments.json); preregistration is [`docs/research/h-apart3-2-cthg-dhc-preregistration-20261028.md`](docs/research/h-apart3-2-cthg-dhc-preregistration-20261028.md).

All scores in this paragraph are **HOLDOUT-DTI**, not live leaderboard scores:

| Evaluator | Withheld positives | CTHG-DHC | 95% CI | 0.2778 reference diagnostic | 95% CI |
|---|---:|---:|---:|---:|---:|
| `GEMSDOE32-HIDE-RECOVER-v3.0` | 22,232 | 0.099651 | [0.087243, 0.111947] | 0.099202 | [0.085951, 0.112668] |
| `GEMSDOE32-HIDE-RECOVER-v3.0-detached-600m` | 15,504 | 0.096026 | [0.083270, 0.109782] | 0.094324 | [0.080945, 0.109425] |
| `GEMSDOE32-SGMC-CAL-v3.0` | 62,703 | 0.082363 | [0.074316, 0.088893] | 0.064121 | [0.056730, 0.071649] |

These measurements are holdout diagnostics of the saved candidate, not confirmed causal/geologic prediction performance. `IR-CTHG-BAND6-TC-02` invalidates the claimed magnetic-tilt mechanism used by this implementation. The small hide-and-recover and detached differences are **not statistically established**: their paired spatial-block 95% CIs include zero. The off-catalogue SGMC-calibrated paired difference is positive in its stored paired interval, but that does not establish a leaderboard score. The score in the DrivenData portal is unknown until a submission is accepted and scored.

### Why the CTHG-DHC GeoTIFF is not promoted

The parallel-run protocol says to check every registry raster and stop if **any** final-dot 3-px overlap exceeds 70%. The earlier scanner summarized “genuine discrete” rasters separately and overlooked dense diagnostic rasters. That was not a valid exemption under the prompt. We corrected the status fail-closed and recorded the duplicate trigger. The calibration lattice is a diagnostic rather than a competition submission, but it is still in the registry and the instruction says “any registry raster”; therefore the current result remains negative. No new placement experiment was run after the three-experiment budget was exhausted.

**Protocol irregularities:** the supplied prompt referred to a “single method paragraph” assigning a lane, but this session did not contain an assigned paragraph. CTHG-DHC was preregistered as a research lane in this repository; do not interpret the result as authorization for a parallel-run slot or competition upload. Additional exploratory placement/holdout sweeps occurred beyond the final three named arms; exact total experiment/time accounting was not retained, so compliance with the three-experiment / two-hour cap is not claimed. No further experiment was run after this discrepancy was recognized.

## Nine-site historical comparison

Scores below are the values supplied by the user / mirrored project records, and are labeled **OWNER-REPORT** unless an organizer receipt is available. No submission-page receipt tying the historical file hash to its reported score is present in this checkout. “Static HOLDOUT-DTI” values are retrospective diagnostics on saved rasters, **not** fold-local model scores and **not** projected leaderboard scores. The page table includes exact pinned filenames, SHAs, pairwise uniqueness and these caveats: [`docs/index.html`](docs/index.html); source data: [`evidence/nine_site_best_files_audit.json`](evidence/nine_site_best_files_audit.json) and [`evidence/nine_site_refreshed_audit_20261028.json`](evidence/nine_site_refreshed_audit_20261028.json).

| Site | Highest supplied live score (OWNER-REPORT) | Historical artifact family | Exact pairwise uniqueness result |
|---|---:|---|---|
| GEMSDOE24 | 0.2477 | H25-1 dotted H19-5 d1.5 | Duplicate within focus set |
| GEMSDOE25 | 0.2600 | H19-5 d2.8 | Duplicate within focus set |
| GEMSDOE27 | 0.2449 | Topo gap-closure d1.5 | Duplicate within focus set |
| GEMSDOE28 | 0.2710 | H36-1 rung30 blind | Duplicate within focus set |
| GEMSDOE30 | 0.2600 | D28 Poisson off-catalogue | Duplicate within focus set |
| GEMSDOE31 | 0.2708 | H27-4 solo d2.8 | Duplicate within focus set |
| GEMSDOE32 | 0.2778 | H33-2-B2 | Duplicate within focus set |
| GEMSDOE33 | 0.2632 | H33d analog tip-stepover | Duplicate within focus set |
| GEMSDOE36 | 0.2750 | Anderson geothermal PINN | Duplicate within focus set |

The pairwise audit flags duplicates under either `|Spearman| > 0.90` or directional 3-px overlap `>70%`. The CTHG-DHC diagnostic is not a substitute for an organizer leaderboard receipt. Do not resubmit these historical files.

## Competition submission procedure

1. **Download only for research while the status above is negative.** The `.tif` and one-file `.zip` are linked in the executive summary. A separate selector must first approve a weekly slot and the strict literal uniqueness gate must pass.
2. After approval, use the competition 306 link supplied in the project: [DrivenData DOE GEMS competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) (the data/submission portal requires authentication). There is a `306` vs `/309/` URL conflict in legacy repository pages; use the official competition 306 page and verify contest identity before uploading.
3. Upload a single-band GeoTIFF or a ZIP containing one GeoTIFF. Use the candidate name and note above only if the selector approves this exact artifact. Save the organizer confirmation receipt and update its status; never infer an organizer score from holdout metrics.
4. Optional local format check: `python scripts/check_submission.py --strict-finite docs/downloads/apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif` (requires the owner-mirrored grid template restored into `data/`).

## Research hypotheses (candidate set, not all validated)

The retrospective analysis plan records candidate layers, transforms, mimics and implementation differences; it is not a valid prospective preregistration. The attempted lane combined:

1. **Intended but not validly implemented:** Cooper–Cowan joint tilt-phase wall should use gravity gradients (Bands 18/11) and verified magnetic fields. The current implementation incorrectly treats Band 6 (`tc`) as magnetic tilt; prior repo forensic records identify it as gamma-ray Total Count. This is logged as `IR-CTHG-BAND6-TC-02`, so no magnetic-tilt claim is made for the current artifact. Intrusive contacts/caldera margins can mimic potential-field contacts.
2. **Fluvial Delta-chi / Laplace throw conduit:** USGS 3DEP 10 m seamless DEM and `dem10_chi_100m_*` with gravity-divergence and basement-depth gradient; target buried range-front faults preserved by upstream knickzones. Unfaulted caprock erosion can mimic it.
3. **MT clay-cap / radon / sinter halo:** Band 17, GeoDAWN radiometrics, GDR #1391 thermal/sinter observations; target hydrothermal conduits where alteration erases topographic scarps. Saline playas, uranium sinks and survey seams can mimic it.
4. **Morris accommodation tensor + curvature / post-sharpened dead moat:** geodetic/seismic Bands 4/7/8/10/16, USGS 3DEP 10 m curvature; target en-echelon relay and stepover accommodation. Road grading, geodetic interpolation halos and lithologic boundaries can mimic it.

These are scientific hypotheses, not claims that geothermal vents or faults have been independently confirmed at every predicted location. The detailed pre-registration explicitly records the named mimics and controls.

## Limitations and next work

- No DrivenData account/session was available, so training assets and `sample_submission.tif` were restored from owner-hosted GitHub mirrors. SHA-256 pins prove mirror integrity only; they do not authenticate those bytes as organizer downloads.
- No organizer receipt, actual live score, or weekly selector action was obtained. Never report HOLDOUT-DTI as ORGANIZER-CONFIRMED.
- Literal registry uniqueness currently fails due >70% overlaps with registered dense/lattice rasters. Fix the shared registry/eligibility policy only if the competition owner or project protocol author explicitly authorizes exclusions; otherwise do not upload this candidate.
- Historical site scores and candidate retrospective raster diagnostics do not provide a reliable leaderboard-score projection. The live metric could depend on undisclosed labels and the organizer's scoring population.
- The supplied prompt reports both `0.3195` and `0.4413` as current leaderboard highs; this conflict was not independently verified and neither value is treated as a confirmed score or target.
- Competition ID mismatch (`306` in the supplied primary source versus legacy `/309/` links) remains an irregularity requiring portal verification before any future upload.
- Next selector action is separate. Do not use a weekly submission slot until exact file hash, registry checks, validated artifact and organizer competition identity are approved.

## Core values

**Maximize P(Win):** choose auditable experiments and fail closed when evidence is insufficient. **Own the outcome:** record negative results, preserve provenance, distinguish diagnostics from organizer scores, and update the gates rather than overstating a result.
