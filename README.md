# ApartGEMSDOE3 — DOE GEMS fault-detection research and audit portal

> **CURRENT RELEASE GATE: `NEGATIVE — DO NOT SUBMIT`**
>
> The latest recorded CFKC GeoTIFF is a format-valid **research artifact**, not an eligible submission. Its final dots have **99.8513%** overlap within 3 px of one pinned registry calibration raster; the earlier BHGC research artifact measures **99.7450%** against that same raster. Both exceed the literal protocol ceiling of **70%**. The independently recorded measurements are in [`evidence/repo_review_20261028.json`](evidence/repo_review_20261028.json) and [`evidence/release_recheck_20261028.json`](evidence/release_recheck_20261028.json); the audit covers one pinned raster, not the full registry.
>
> **Research-only TIFs—not for competition upload:** [CFKC-DHC](docs/downloads/apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif) · [BHGC-3](docs/downloads/apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif). Format/grid/range passed against an integrity-pinned **owner-supplied mirror**, not an organizer-authenticated template. The uniqueness gate failed for both.
>
> **No file is authorized for submission.** No new experiment or TIFF was generated: the prompt's referenced method paragraph/lane is not identified, and the full training feature stack is absent. No weekly slot was used. Historical `HOLDOUT-DTI` results are local diagnostics, not leaderboard score estimates; the 0.2778 figure remains `OWNER-REPORT` without a receipt/hash link in this checkout.
>
> See the [current release status](docs/release-status.html), [comprehensive repository review](docs/research/repo-review-20261028.md), [four-hypothesis shortlist](docs/review.html), [executive summary](docs/executive-summary.html), and [review evidence](evidence/repo_review_20261028.json).


![ApartGEMSDOE3 4-Panel Diagnostic Figure](docs/assets/fig_bhgc_apart3.png)

---

## 1. Historical 9-Site Focus Audit (scores are owner-reported unless a receipt is linked)

The rows below preserve historical figures from user/owner reports and local audit artifacts; they are not a fresh official leaderboard read. The 0.2778 receipt-to-raster linkage has not been independently established here. Holdout diagnostics are `HOLDOUT-DTI` and are never leaderboard-score projections. Candidate uniqueness numbers below came from a former filtered-registry comparison and are not literal all-registry clearance; no current row authorizes resubmission.

| Site / Repository | Highest-scoring historical reference (do not resubmit) | Reported live score provenance | `HOLDOUT-DTI`: `GEMSDOE32-HIDE-RECOVER-v3.0` (`n=22,232`) [95% CI] | `HOLDOUT-DTI`: `GEMSDOE32-SGMC-CAL-v3.0` (`n=62,703`) [95% CI] | Uniqueness vs Registry (`<= 70%` 3-px & `|ρ| <= 0.90`) | Gate Decision |
|---|---|---|---|---|---|---|
| **ApartGEMSDOE3 (research artifacts)** | Latest: [`CFKC-DHC`](docs/downloads/apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif); earlier: [`BHGC-3`](docs/downloads/apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif) | — | Both `HOLDOUT-DTI` results are historical local diagnostics, not score predictions | — | **NOT UNIQUE under literal registry test (CFKC 99.8513%; BHGC 99.7450% vs one pinned lattice)** | **DO NOT SUBMIT** |
| **[GEMSDOE32](https://github.com/buffedlizard55-lab/GEMSDOE32)** | *Hist:* [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) (`37,654`d)<br>*Cand:* `gemsdoe32-h48-fbgr-dualcover-axial28-37654-20261027T180500Z-4d38a240-zeros.tif` (`37,654`d) | **`0.2778`** (`OWNER-REPORT`; organizer receipt/hash linkage absent)<br>*Cand:* unsubmitted | *Hist:* `0.099202` `[0.085951, 0.112668]`<br>*Cand:* `0.008074` static (`0.115341` OOF) | *Hist:* `0.064121` `[0.056730, 0.071649]`<br>*Cand:* `0.056798` `[0.039821, 0.072947]` | *Hist:* **DUPLICATE** (`100.0%` self)<br>*Cand:* filtered-screen pass only (`44.14%` vs Champ), loses SGMC | *Hist:* Reference Only<br>*Cand:* Loses SGMC vs Champ |
| **[GEMSDOE36](https://github.com/buffedlizard55-lab/GEMSDOE36)** | *Hist:* `gemsdoe36-h37-1-b2-weld-r4-add1200-20261006T031727Z-f0671645-zeros.tif` (`38,854`d)<br>*Cand:* `gems36-h36-3-sgrt-oof-submod31-20261027T161257Z-3698dc0f-zeros.tif` (`39,986`d) | **`0.2750`** (`OWNER-REPORT`)<br>*Cand:* unsubmitted | *Hist:* `0.098950`<br>*Cand:* `0.015984` `[0.011064, 0.021161]` | *Hist:* `0.063990`<br>*Cand:* `0.061213` `[0.043934, 0.076453]` | *Hist:* **DUPLICATE** (`96.91%` vs Champ)<br>*Cand:* filtered-screen pass only (`39.00%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Below Champ on SGMC |
| **[GEMSDOE28](https://github.com/buffedlizard55-lab/GEMSDOE28)** | *Hist:* `gemsdoe28-h33-h33-4-b2-p95-20261004T220000Z-ac877a14-zeros.tif` (`37,660`d)<br>*Cand:* `gems28-s21-agsp-e3-bipop-37654-20261027T174500Z-eb751b64-zeros.tif` (`37,654`d) | **`0.2710`** (`OWNER-REPORT`)<br>*Cand:* unsubmitted | *Hist:* `0.098110`<br>*Cand:* `0.008074` `[0.005681, 0.010602]` | *Hist:* `0.063890`<br>*Cand:* `0.056607` `[0.039815, 0.072578]` | *Hist:* **DUPLICATE** (`96.82%` vs Champ)<br>*Cand:* filtered-screen pass only (`44.14%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Loses SGMC vs Champ |
| **[GEMSDOE31](https://github.com/buffedlizard55-lab/GEMSDOE31)** | *Hist:* `gemsdoe31-h31-4-b1-20261004-ab03e521-zeros.tif` (`40,199`d)<br>*Cand:* `gemsdoe31-h1-updip-grav-37654-20261027T170812Z-bc061152-zeros.tif` (`37,654`d) | **`0.2708`** (`OWNER-REPORT`)<br>*Cand:* unsubmitted | *Hist:* `0.098004`<br>*Cand:* `0.009145` `[0.006127, 0.012183]` | *Hist:* `0.063510`<br>*Cand:* `0.057491` `[0.041335, 0.072855]` | *Hist:* **DUPLICATE** (`100.0%` vs Champ)<br>*Cand:* filtered-screen pass only (`41.49%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Loses SGMC vs Champ |
| **[GEMSDOE33](https://github.com/buffedlizard55-lab/GEMSDOE33)** | *Hist:* `gems33-h31-1-d3-0-20261003-990233092b07-allfinite.tif` (`41,865`d)<br>*Cand:* `gemsdoe33-h33-updip-mt-celf-20261027T171422Z-548fa4e9-zeros.tif` (`40,342`d) | **`0.2632`** (`OWNER-REPORT`)<br>*Cand:* unsubmitted | *Hist:* `0.096410`<br>*Cand:* `0.036570` `[0.029754, 0.043400]` | *Hist:* `0.062980`<br>*Cand:* `0.062260` `[0.045798, 0.077276]` | *Hist:* **DUPLICATE** (`94.10%` vs Champ)<br>*Cand:* filtered-screen pass only (`39.04%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Below Champ on SGMC |
| **[GEMSDOE25](https://github.com/buffedlizard55-lab/GEMSDOE25)** | *Hist:* `gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`44,090`d)<br>*Cand:* `gems25-h66-dualcover-gpca-mfull71-msub58-celf28-37654-20261026T221849Z-1f4979fb-zeros.tif` (`37,654`d) | **`0.2600`** (`OWNER-REPORT`)<br>*Cand:* unsubmitted | *Hist:* `0.095620`<br>*Cand:* `0.008074` `[0.005681, 0.010602]` | *Hist:* `0.062140`<br>*Cand:* `0.056607` `[0.039815, 0.072578]` | *Hist:* **DUPLICATE** (`100.0%` vs Champ)<br>*Cand:* filtered-screen pass only (`44.14%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Loses SGMC vs Champ |
| **[GEMSDOE30](https://github.com/buffedlizard55-lab/GEMSDOE30)** | *Hist:* `gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`44,090`d)<br>*Cand:* `gems30-h1-updip-3dep10m-scarp-20261027T173000Z-39ca38c9-zeros.tif` (`37,654`d) | **`0.2600`** (`OWNER-REPORT`)<br>*Cand:* unsubmitted | *Hist:* `0.095620`<br>*Cand:* `0.055436` `[0.044572, 0.065997]` | *Hist:* `0.062140`<br>*Cand:* `0.047218` `[0.033245, 0.059880]` | *Hist:* **DUPLICATE** (`100.0%` vs Champ)<br>*Cand:* filtered-screen pass only (`25.81%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Low SGMC (`0.0472`) |
| **[GEMSDOE24](https://github.com/buffedlizard55-lab/GEMSDOE24)** | *Hist:* `gems24-h25-1-dotted-h19-5-d1-5-20261002-7a0ba5a67b87-nan.tif` (`60,069`d)<br>*Cand:* `24gems-blind-upwelling-20261026T162611Z-a23f2207f2c0-zeros.tif` (`37,722`d) | **`0.2477`** (`OWNER-REPORT`)<br>*Cand:* unsubmitted | *Hist:* `0.088231`<br>*Cand:* `0.040870` `[0.031516, 0.049594]` | *Hist:* `0.056895`<br>*Cand:* `0.057266` `[0.039164, 0.075009]` | *Hist:* **DUPLICATE** (`100.0%` vs Champ)<br>*Cand:* filtered-screen pass only (`17.70%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Low HR & SGMC |
| **[GEMSDOE27](https://github.com/buffedlizard55-lab/GEMSDOE27)** | *Hist:* `gems23-h23-3-corridor-skeleton-t022-20261002-4cc45fb4-nan.tif` (`61,328`d)<br>*Cand:* `gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif` (`38,105`d) | **`0.2449`** (`OWNER-REPORT`; `H31-DRCG`: **`0.2250`** `OWNER-REPORT`) | *Hist:* `0.089410`<br>*Cand:* `0.008564` `[0.005975, 0.011056]` | *Hist:* `0.058110`<br>*Cand:* `0.061986` `[0.044314, 0.078556]` | *Hist:* **DUPLICATE** (`86.70%` vs Champ)<br>*Cand:* filtered-screen pass only (`50.23%` vs Champ) | *Hist:* Do Not Resubmit<br>*Cand:* Scored `0.2250` live |

### Submission status and safe workflow
**Do not upload either current candidate.** The programmatic validator only checks file format, grid and values; it does not certify scientific quality, uniqueness, score, or weekly-slot authorization. A future candidate may use the official [competition 306 submissions page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/) only after the exact saved TIFF passes the literal all-registry surface and final-dot tests, the holdout/paired-improvement gates, and separate selector approval. Current filename, submission name, and note are retained for audit only; they are not an upload recommendation.

---

## 2. Deep PhD Analysis: Why `GEMSDOE32` Scored `0.2778`, How `0.3195` / `0.4413` Were Reached, and Why the BHGC research artifact is not submission-cleared

### 2.1 Exact 4-Step Nested Ablation Chain Behind `0.2778` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`)
The local forensic audit (`evidence/livescore_forensics_20261027.json`) reports a nested H19-5 family behind these submissions. Scores remain owner-reported absent a linked organizer receipt; the analysis is a metric-consistent explanation, not proof that thinning alone caused each score gain:
1. **Step 0 (`H19-5`, `121,131` px -> `0.1922` `OWNER-REPORT`):** Dense multi-physics ridge/openness/thermal corridor ribbon.
2. **Step 1 (`d = 1.5 px` Poisson-disk thinning, `60,069` px -> `0.2477` `OWNER-REPORT` on `GEMSDOE24`):** Because $\text{TP}_w = \sum_{y \in G} \max_{x}[p(x)\,k(d(x, y))]$ takes a maximum over the $300\text{ m}$ ($3\text{ px}$) kernel while $\alpha\,\text{FP}_w = 0.2 \sum_{x} p(x)(1 - k(d(x, G)))$ sums linearly over every emitted pixel, thinning adjacent $100\text{ m}$ ridge pixels removes redundant false-positive mass and jumps `+0.0555`.
3. **Step 2 (`d = 2.8 px` Kernel-matched Poisson-disk thinning, `44,090` px -> `0.2600` `OWNER-REPORT` on `GEMSDOE25/30`):** Matching the inter-dot spacing ($280\text{ m}$) to the $300\text{ m}$ triangular kernel radius adds `+0.0123`.
4. **Step 3 (`B = 1 px` Catalogue Collar Pruning, `40,199` px -> `0.2708` `OWNER-REPORT` on `GEMSDOE31`):** Removing `3,891` dots within $100\text{ m}$ of `labels.tif` adds `+0.0108`.
5. **Step 4 (`B = 2 px` Catalogue Collar Pruning, `37,654` px -> `0.2778` `OWNER-REPORT` on `GEMSDOE32` (no receipt/hash linkage in this checkout)):** Removing `2,545` additional dots within $200\text{ m}$ of `labels.tif` was associated with a reported `0.2778`; the collar-density explanation is a local interpretation, not an independently verified causal finding.

### 2.2 What the prior BHGC experiment suggests (not a promotion result)
The following is a hypothesis supported by local holdout diagnostics, not a leaderboard-score claim. Its old “unique” status used a filtered registry and is superseded by the literal all-registry audit:
- **Near-Collar OOF Models (`GEMSDOE32 H48-1 FBGR`, `KANLERGEMSDOE3`, `WBGGEMSDOE3`, `GEMSDOEkarage3`):** Achieved `0.1153–0.1160` on `Hide-and-Recover` (`31.2%` of withheld pixels at $\le 6\text{ px}$, `70.6%` at $\le 15\text{ px}$), but dropped to `0.0568–0.0573` on untouched Off-Catalogue `SGMC_cal` (below the `0.2778` Champion's `0.064121`) because they placed `57%–72%` of their dots within $1.5\text{ km}$ of `labels.tif`.
- **`H-APART-1 (BHGC-3)` Solution:** Combines 6 new label-free Laplace-harmonic gravity divergence, magnetic tilt zero-crossing, de-confounded piedmont-horst, transtensional accommodation, and hydrothermal clay-cap/$^{214}\text{Bi}$ radon channels (`bhgc_extra_6ch.npy`) with an 89-ch/76-ch Dual-Cover OOF classifier and a **3-Zone Radial Bi-Population Transfer Function** (`Zone 1` collar depletion at $2.0 < d_{\text{vis}} \le 5.5\text{ px}$; `Zone 2` detached-segment & accommodation bridge amplification at $5.2 < d_{\text{vis}} \le 22.0\text{ px}$; `Zone 3` far-field structural-geothermal spine floor at $d_{\text{vis}} > 21.8\text{ px}$) plus axial crest spacing $d_{\min} = 3.22\text{ px}$.

---

## 3. Controlled 3-Experiment Ablation Ledger (`evidence/bhgc_experiments.json`)

| Arm / Experiment | `GEMSDOE32-HIDE-RECOVER-v3.0` (`n=22,232`) `HOLDOUT-DTI` [95% CI] | `Detached >= 600 m` (`n=15,504`) `HOLDOUT-DTI` [95% CI] | `GEMSDOE32-SGMC-CAL-v3.0` (`n=62,703`) `HOLDOUT-DTI` [95% CI] | `Censored d_hid > 2 px` (`n=19,179`) `HOLDOUT-DTI` [95% CI] | Beats `0.2778` Champion on HR, Detached & SGMC? |
|---|---|---|---|---|---|
| **Baseline 1: `0.2778` Champion (`h33-2-b2`)** | `0.099202` `[0.085951, 0.112668]` | `0.094324` `[0.079248, 0.109825]` | `0.064121` `[0.056730, 0.071649]` | `0.004515` `[0.003711, 0.005375]` | Reference Incumbent |
| **Baseline 2: `GEMSDOE32 H48-1 FBGR` (`4d38a240`)** | `0.115341` `[0.100353, 0.129771]` | `0.101168` `[0.086145, 0.116634]` | `0.056798` `[0.050449, 0.063890]` | `0.004628` `[0.003835, 0.005471]` | No (loses SGMC by `-0.007323`) |
| **`EXP-1: BHGC-Unsup-Spine`** (Label-free 6-ch `BHGC` spine + visible tip relay) | `0.047273` `[0.039402, 0.054949]` | `0.041998` `[0.034250, 0.050032]` | **`0.084765`** `[0.075139, 0.093338]` | `0.002011` `[0.001580, 0.002462]` | No (wins SGMC `+32.2%`, loses HR) |
| **`EXP-2: BHGC-OOF-Near`** (89ch/76ch Dual-Cover OOF, `w_far=0`) | **`0.116105`** `[0.100991, 0.130320]` | **`0.101235`** `[0.085873, 0.116952]` | `0.057482` `[0.050827, 0.064354]` | **`0.004637`** `[0.003846, 0.005476]` | No (beats `H48-1` on all 3, loses SGMC vs Champ) |
| **`EXP-3: H-APART-1 (BHGC-3)` (historical experiment; release decision superseded)** | **`0.101735`** `[0.088171, 0.114724]` (`+0.002533` vs Champ) | **`0.095807`** `[0.081047, 0.110344]` (`+0.001483` vs Champ) | **`0.070897`** `[0.063401, 0.077404]` (`+0.006776` / **`+10.57%`** vs Champ) | `0.003798` `[0.003169, 0.004470]` | **Not promoted: paired 95% intervals cross zero; strict registry uniqueness fails.** |

---

## 4. Reproducible CLI Commands

```bash
# 1. Restore & SHA-256 verify all 30 competition, USGS/GDR external, and historical scored files
.venv/bin/python scripts/restore_data.py --group all

# 2. Restore 583-entry cross-site & sibling-org uniqueness registry
.venv/bin/python scripts/restore_pinned_registry.py

# 3. Run the end-to-end H-APART-1 (BHGC-3) pipeline (89-ch canary, 3 experiments, uniqueness gates, GeoTIFF emission)
.venv/bin/python scripts/run_bhgc_pipeline.py

# 4. Run standalone strict GeoTIFF validator and pytest suite
.venv/bin/python scripts/check_submission.py --strict-finite \
  docs/downloads/apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif
.venv/bin/pytest -q

# 5. Rebuild GitHub Pages portal under docs/
.venv/bin/python scripts/build_site.py
```

---

## 5. Required JSON Run Card (`run_card.json`)

Historical BHGC metrics are saved at [`run_card.json`](run_card.json) and [`evidence/bhgc_run_card.json`](evidence/bhgc_run_card.json); current release eligibility is recorded in [`evidence/repo_review_20261028.json`](evidence/repo_review_20261028.json):
- **`hypothesis`:** `H-APART-1 (BHGC-3): Laplace-Harmonic Gravity-Vector Divergence (Band 18, Band 11), Depth-Invariant Magnetic Tilt Zero-Crossing Wall, Multi-Scale Piedmont-Horst Bedrock Contact Spine & PU-Safe 89-Ch/76-Ch Dual-Cover Hydrothermal-Vent OOF with Axial-Crest Submodular Emission`
- **`raster_sha256`:** `ba092640a4f776e3a22c8af1a5fe503487d4fa3f2277020a6e8268fd08e0797a`
- **`submission_name`:** `APARTGEMSDOE3-BHGC3-AB6646B7`
- **`submission_note` (`74/140` chars):** `Apart3 H-APART-1 BHGC-3 bipop d3.22 37654d B2 | HR=0.1017 SGMC=0.0709`
- **`verdict`:** `"negative"` under the 2026-10-28 literal registry audit

---

## 6. Standing User Prompt & Parallel-Run Protocol Charter

<details>
<summary>Click to view the verbatim project prompt & Parallel-Run Protocol instructions</summary>

```text
Please put this prompt into the repo README.md, complete any pending work, and keep working on the next steps autonomously.
Download the required data from the official competition, and prepare the data for our training and inference pipeline automatically.

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
