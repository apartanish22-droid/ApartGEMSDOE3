#!/usr/bin/env python3
"""Build distinct fail-closed public pages from the audited repository records."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("release-status.html", "Release status"),
    ("submissions.html", "How to submit"),
    ("research.html", "Research"),
    ("hypotheses.html", "Hypotheses"),
    ("leaderboard.html", "Score audit"),
    ("review.html", "Repository review"),
    ("sources.html", "Sources"),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def repo_link(path: str) -> str:
    return "https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/" + path.lstrip("/")


def page(title: str, body: str, *, prefix: str = "") -> str:
    links = "".join(
        f'<a href="{prefix}{esc(path)}">{esc(label)}</a>' for path, label in NAV
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · ApartGEMSDOE3</title>
<style>
:root{{color-scheme:dark;--bg:#0b1220;--panel:#142238;--line:#30415c;--text:#e8edf7;--muted:#a8b7cc;--link:#8bd7fa;--alert:#4b2025}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 system-ui,sans-serif}}
header{{background:#111f35;border-bottom:1px solid var(--line)}}.wrap{{max-width:1120px;margin:auto;padding:20px}}
.brand{{color:#8bd7fa;letter-spacing:.12em;font-size:.82rem}}h1{{margin:.15em 0;font-size:2.2rem}}h2{{margin-top:0}}nav{{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:14px}}a{{color:var(--link)}}nav a{{text-decoration:none}}main section{{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:18px 0;padding:22px}}
.alert{{padding:16px;background:var(--alert);border:1px solid #e47b82;border-radius:8px}}.muted{{color:var(--muted)}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:780px}}th,td{{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid var(--line)}}code{{overflow-wrap:anywhere;color:#fff}}li{{margin:.45em 0}}
</style></head><body><header><div class="wrap"><div class="brand">APARTGEMSDOE3 · RESEARCH / RELEASE REVIEW</div><h1>{esc(title)}</h1><nav aria-label="Main navigation">{links}</nav></div></header>
<main class="wrap">{body}</main></body></html>\n'''


def sync_status_artifacts(root: Path = ROOT) -> dict:
    """Keep public feed/run-card copies aligned with the single current status record."""
    status = json.loads((root / "registry/current_status.json").read_text())
    card_path = root / status["current_run_card"]
    card = json.loads(card_path.read_text())
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise ValueError("Public status builder requires a fail-closed negative current card")
    if status.get("any_file_ok_to_submit") is not False:
        raise ValueError("Public status builder refuses a current status that authorizes a file")

    current = status["current_candidate"]
    if card.get("candidate_id") != current.get("candidate_id"):
        raise ValueError("Current status candidate and current evidence card disagree")
    artifact_path = card.get("artifact_path") or card.get("artifacts", {}).get("primary_zeros_tif")
    raster_sha256 = card.get("raster_sha256") or card.get("artifacts", {}).get("primary_zeros_sha256")
    if not artifact_path or raster_sha256 != current.get("sha256"):
        raise ValueError("Current candidate artifact/hash is incomplete or inconsistent")

    card["release_status"] = card.get("verdict", "negative")
    card["ok_to_download_as_submission"] = False
    latest_path = root / "docs/data/latest-run-card.json"
    latest_path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    site_data_path = root / "docs/assets/site-data.json"
    site_data = json.loads(site_data_path.read_text())
    site_data["run_card"] = card
    site_data_path.write_text(json.dumps(site_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    feed_path = root / "docs/data/feed.json"
    feed = json.loads(feed_path.read_text())
    feed["generated_utc"] = status["updated_utc"]
    feed["current_status"] = status
    feed["current_candidate"] = {
        "run_card": status["current_run_card"],
        "experiments": None,
        "registry_audit": None,
        "verdict": card["verdict"],
        "ok_to_submit": card["ok_to_submit"],
    }
    feed["submission"] = {
        "candidate_id": current["candidate_id"],
        "file": artifact_path,
        "sha256": raster_sha256,
        "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "download_ok_for_research": card.get("download_for_research_ok", card.get("download_ok_for_audit_only", False)),
        "ok_to_submit": card["ok_to_submit"],
        "slot_used": card.get("slot_used", False),
        "selector_required": card["selector_required"],
        "verdict": card["verdict"],
    }
    feed_path.write_text(json.dumps(feed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return card


def calibration_summary(root: Path = ROOT) -> str:
    """HTML block for the pre-registered live-ledger calibration (evidence/ledger_calibration_check_20261030.json)."""
    path = root / "evidence" / "ledger_calibration_check_20261030.json"
    if not path.is_file():
        return '<p class="muted">Calibration check not recorded.</p>'
    d = json.loads(path.read_text(encoding="utf-8"))
    h = d["spearman_owner_vs_holdout_pooled"]
    g = d["spearman_owner_vs_sgmc_prevalence_calibrated"]
    return (
        '<section class="alert"><h2>Calibration (pre-registered, n=117 live-ledger rasters)</h2>'
        f"<p>Owner-reported live scores (OWNER-REPORT) against the repo's evaluator outputs (HOLDOUT-DTI). "
        f"The off-catalogue SGMC-calibrated proxy is <b>positively and significantly</b> rank-correlated with the scores: "
        f"rho={float(g['rho']):+.2f}, 95% bootstrap CI [{float(g['bootstrap_ci95'][0]):+.2f}, {float(g['bootstrap_ci95'][1]):+.2f}], p={float(g['p_value']):.1e}. "
        f"The hide-and-recover HOLDOUT-DTI is <b>not significant</b>: rho={float(h['rho']):+.2f}, 95% CI [{float(h['bootstrap_ci95'][0]):+.2f}, {float(h['bootstrap_ci95'][1]):+.2f}], p={float(h['p_value']):.2f}. "
        "An earlier n=18 check had shown a negative holdout correlation. It did not hold at n=117 and is withdrawn. "
        "This is a rank diagnostic for ordering candidates, not a score projection. "
        f'Evidence: <a href="{esc(repo_link("evidence/ledger_calibration_check_20261030.json"))}">ledger_calibration_check_20261030.json</a>.</p></section>'
    )


def verification_record(root: Path = ROOT) -> dict:
    """Load the byte-level nine-site verification record (evidence/nine_site_verification_20261030.json)."""
    return json.loads((root / "evidence/nine_site_verification_20261030.json").read_text(encoding="utf-8"))


def candidate_under_review_html(root: Path = ROOT) -> str:
    """Fail-closed block for H-SEISMIC (no download CTA). Numbers read from its run card."""
    path = root / "evidence" / "GEMSDOE32-H-SEISMIC-20261030T020420Z-run-card.json"
    if not path.is_file():
        return ""
    card = json.loads(path.read_text(encoding="utf-8"))
    hv = card["holdout"]["visible_gated_v3"]
    sg = card["holdout"]["sgmc_off_catalogue"]
    ci = hv.get("ci95", [])
    return (
        '<section class="alert"><h2>Candidate under review: H-SEISMIC (NOT cleared)</h2>'
        "<p><b>Do not download or submit this file.</b> It is format-valid and passes the leakage canaries. "
        f"Its pooled HOLDOUT-DTI is <b>{float(hv['pooled_dti']):.5f}</b> [{float(ci[0]):.5f}, {float(ci[1]):.5f}] "
        "(evaluator GEMSDOE32-HOLDOUT-v3-visible-gated). The current holdout best is the GEMSDOE32 file at 0.004515, so the gate is failed. "
        f"Its SGMC-calibrated off-catalogue DTI is {float(sg['sgmc_prevalence_calibrated_dti']):.4f} against 0.0641 for GEMSDOE32. "
        "That metric is the one the pre-registered n = 117 test supports, so this is an owner decision under proposal V1, not a selector promotion. "
        "Uniqueness was checked against 15 locally available comparators only; the full-registry check was not run. "
        "The run card's ok_to_submit flag is overridden by the gate. "
        f'<a href="{esc(repo_link("evidence/GEMSDOE32-H-SEISMIC-20261030T020420Z-run-card.json"))}">Run card</a>.</p></section>'
    )


def start_here_html(root: Path = ROOT) -> str:
    """Executive answer and per-site download/estimate/uniqueness table (fail-closed; no download CTA)."""
    rec = verification_record(root)
    names = [row["site"] for row in rec["sites"]]
    overlap = rec["pairwise_3px_overlap_row_within_3px_of_column"]
    rows = []
    for row in rec["sites"]:
        site = row["site"]
        peers = [(other, overlap[f"{site}->{other}"]) for other in names if other != site]
        peer, pct = max(peers, key=lambda x: x[1])
        if site == "GEMSDOE32":
            download = "<b>NO</b> — already submitted per the registry record; resubmitting adds nothing."
        elif site == "GEMSDOE30":
            download = "<b>NO</b> — same prediction as GEMSDOE25 (identical after NaN→0)."
        elif not row["validator_strict_finite_passed"]:
            download = "<b>NO</b> — fails the strict finite [0,1] check (NaN outside footprint). Do not re-save as zeros."
        else:
            download = "<b>NO</b> — not unique (see right) and no authorization."
        hold = row["holdout_dti"]
        ci = hold["ci95_cluster_bootstrap"]
        rows.append(
            "<tr>"
            f"<td>{esc(site)}</td>"
            f"<td><code>{esc(row['file_name'])}</code><br><span class=\"muted\">File to download: NONE</span></td>"
            f"<td>OWNER-REPORT {float(row['owner_reported_score_OWNER_REPORT']):.4f}</td>"
            f"<td>HOLDOUT-DTI {hold['pooled_dti']:.4f} [{ci[0]:.4f}, {ci[1]:.4f}], n={hold['withheld_positives']:,} withheld</td>"
            "<td>Not estimable</td>"
            f"<td>NOT UNIQUE: {pct:.2%} of dots within 3 px of {esc(peer)}</td>"
            f"<td>{download}</td></tr>"
        )
    table = (
        '<div class="scroll"><table><thead><tr><th>Site</th><th>File (for reference only)</th>'
        '<th>Reported score</th><th>Holdout DTI (evaluator v3.0, 95% CI)</th><th>Estimated score for a new file</th>'
        '<th>Unique?</th><th>Download and submit now?</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
    )
    best = max(rec["sites"], key=lambda r: r["owner_reported_score_OWNER_REPORT"])
    corr = rec["correlations"]
    return (
        '<section class="alert"><h2>Start here: the verified answer</h2>'
        "<p><b>No file in this repository is cleared to download or submit.</b> "
        f"Highest reported file: <b>{esc(best['site'])} {float(best['owner_reported_score_OWNER_REPORT']):.4f}</b> (OWNER-REPORT). "
        "It is already submitted per the registry record and is not unique against the other eight. "
        "<b>No new TIF was generated</b>: the protocol lane paragraph is absent, the full 451-raster uniqueness check has not been run, "
        "and no candidate has passed holdout validation.</p>"
        "<p><b>Portal error “Predicted values must be in range [0, 1]”:</b> five site files (GEMSDOE24, 25, 27, 28, 31) "
        "have NaN outside the footprint and fail the repo’s strict check. The official spec allows NaN outside the bounds, "
        "so the cause of the portal message is <b>unverified</b>. Do not re-save a file to get past it: that is a copy of an existing submission.</p>"
        "<p><b>Leaderboard:</b> public #1 is xiaofanhu 0.4544 (PUBLIC-LEADERBOARD-OBSERVATION, read 2026-10-30). "
        "The prompts state 0.4413 and 0.3195; these values conflict and are flagged for review.</p>"
        f"<p><b>Why the top file scored well (association, n=9):</b> share of dots more than 1 km from the catalogue vs owner score "
        f"ρ = {corr['spearman_owner_vs_frac_beyond_1km']['rho']:+.2f}. The catalogue-withheld holdout ranks the files in reverse "
        f"(n=9, ρ = {corr['spearman_owner_vs_holdout_dti']['rho']:+.2f}). A pre-registered test on n=117 live-ledger rasters does not support that holdout ranking (ρ = +0.17, CI spans 0); see the calibration block. Do not use the hide-and-recover holdout alone to select a candidate.</p>"
        f'<p><a href="{esc(repo_link("docs/research/nine-site-verification-20261030.md"))}">Full verification, analysis, hypotheses, and run card</a> · '
        f'<a href="{esc(repo_link("evidence/nine_site_verification_20261030.json"))}">Byte-level evidence (JSON)</a> · '
        f'<a href="{esc(repo_link("scripts/verify_nine_site.py"))}">Reproduce script</a></p></section>'
        '<section><h2>Per-site download, estimate, and uniqueness</h2>'
        "<p>Estimate for any new file: <b>not estimable</b>. Unique: <b>no</b> for all nine.</p>"
        + table
        + "</section>"
    )



# Session 2026-10-31 decision block (static, reviewed text). Numbers trace to evidence/ files; see tests/test_session_20261031_decision.py.
DECISION_HTML_20261031 = '''<section class="alert" id="decision"><h2>SUBMISSION DECISION (31 Oct 2026) — read this first</h2>
<p style="font-size:1.1rem"><b>Download: NONE. Submit: NONE.</b> No file on this site is cleared to download or submit. There is no download button for any candidate on this page, on purpose: every candidate fails at least one automated gate. Verified from bytes this session; every number is labelled.</p>
<div class="scroll"><table><thead><tr><th>Item</th><th>File</th><th>Score (label)</th><th>Unique?</th><th>Format: finite, [0,1], no NaN</th><th>Verdict</th></tr></thead><tbody>
<tr><td><b>Highest reported score</b></td><td><code>gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code><br>SHA-256 <code>c55bafc4…ab6fa9</code></td><td>0.2778 OWNER-REPORT (no organizer receipt in repo)</td><td><b>No</b>: 97.3%+ overlap with every other focus site (all 36 pairs, one direction)</td><td>Yes</td><td><b>DO NOT RESUBMIT.</b> Already on the board; a resubmission is a duplicate.</td></tr>
<tr><td><b>Best NaN-free zero-fill of the GEMSDOE36 family</b></td><td>GEMSDOE36 <code>…9b9ea4e6-zeros.tif</code></td><td>0.2750 OWNER-REPORT</td><td><b>No</b>: same family as GEMSDOE32</td><td>Yes</td><td>Do not submit (duplicate family).</td></tr>
<tr><td><b>New candidate E1 (this session)</b>: Euler N=1 solution density on TMI, 37,654 dots</td><td><code>E1-EULER-N1-TMI-37654.tif</code>, SHA-256 <code>62b8004758…4db9ec</code>; not published to downloads</td><td><b>Not estimable.</b> HOLDOUT-DTI HIDE-RECOVER 0.0196 [0.0157, 0.0236] (n=22,232; passes, but non-discriminating, IR-4); SGMC-CAL 0.0147 [0.0123, 0.0171] (n=62,703). ANALOG PROJECTION only (not a score): about 0.02, range 0.00–0.045, from 13 owner-reported rasters with the same SGMC-calibrated value</td><td><b>Fails</b> the literal rule: 4 of 131 registry rasters flagged (metric artifact, see IR-3)</td><td>Yes</td><td><b>NEGATIVE. DO NOT SUBMIT.</b> Fails SGMC-calibrated non-regression: 0.0147 [0.0123, 0.0171] vs champion 0.0641; below random-dot control 0.046–0.047.</td></tr>
<tr><td><b>Branch-merged candidate H-GEO-1</b> (from main, 2026-10-31)</td><td><code>gemsdoe32-hgeo1-crossgrad-37654d-20261031T045529Z-2940f96e-zeros.tif</code>, SHA-256 <code>71c95fd0…ca113</code></td><td><b>Not estimable.</b> HOLDOUT-DTI HIDE-RECOVER 0.0053 [0.0039, 0.0069] (GEMSDOE32-HIDE-RECOVER-v3.0, n=22,232). SGMC-CAL 0.0405 [0.0321, 0.0490] (n=62,703) vs champion 0.0641: a regression.</td><td><b>No.</b> 7 of 131 registry rasters flagged; worst 99.94% within 3 px of the 13GEMSDOE lattice (<a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/arena/8d33bc2d-apartgemsdoe3/evidence/hgeo1_uniqueness_recheck_20261031.json">evidence</a>). The brief's "UNIQUE (max 46.24%)" is not reproduced.</td><td>Yes</td><td><b>DO NOT DOWNLOAD AS SUBMISSION.</b> Fails uniqueness and SGMC non-regression. Its card's "promote" verdict conflicts with its own fields (IR-13).</td></tr>
<tr><td><b>Branch-merged candidate H1-LIDAR-SCARP-DEM-CHI</b> (from main)</td><td><code>gemsdoe32-h1-lidar-scarp-dem-chi-20261031T044640Z-6660ab7a-zeros.tif</code>, SHA-256 <code>3ec64572…5a9abc</code></td><td><b>Not estimable.</b> HOLDOUT-DTI 0.0062 [0.0047, 0.0074] (evaluator GEMSDOE32-HOLDOUT-v3-visible-gated, n=22,232; label differs from E1, IR-14). Leakage canaries not run.</td><td><b>No.</b> 7 of 131 registry rasters flagged; worst 99.78% within 3 px of the 13GEMSDOE lattice (<a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/arena/8d33bc2d-apartgemsdoe3/evidence/h1_uniqueness_recheck_20261031.json">evidence</a>).</td><td>Yes (per card)</td><td><b>RESEARCH ONLY, NOT A SUBMISSION.</b> Its card says ok_to_submit=false and ok_to_download_as_submission=false. The main-branch "OK TO DOWNLOAD ONLY" banner is withdrawn.</td></tr>
</tbody></table></div>
<p><b>Withdrawn on main:</b> main (commit c1990a7 and its merges) showed "Download: YES" for H-GEO-1 and "OK TO DOWNLOAD ONLY" for H1 on the executive summary and index pages. Both statements contradict the registry (<code>any_file_ok_to_submit=false</code>) and fail the uniqueness gate, so they are removed here. The files stay in <code>docs/downloads/</code> for audit only.</p><p><b>Why no unique, high-scoring file exists yet:</b> the nine focus files are one family (all pairs overlap, lowest 97.3%). The only new, catalogue-free candidate this session (E1) fails the scientific gate. Random dots beat E1 on the metric that matters. Every gate is automated; none requires human inspection.</p>
<p class="muted">Evidence: <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/evidence/euler_n1_E1_run_card.json">E1 run card</a> · <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/docs/research/preregistration-euler-n1-tmi-20261031.md">E1 pre-registration</a> · <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/evidence/random_dot_controls_20261031.json">random-dot controls</a> · <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/evidence/champion_catalogue_proximity_20261031.json">catalogue-proximity table</a> · <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/docs/research/session-20261031-e1-euler-review.md">full session review</a></p>
</section>
<section><h2>Why 0.2778 scored highest — verified from bytes</h2>
<ul>
<li><b>Dot chain (count of positive pixels, from the files):</b> H19-5 121,131 → d1.5 60,069 → d2.8 44,090 → champion 37,654. Each file is a subset of its parent.</li>
<li><b>The champion is d2.8 with exactly 6,436 dots removed:</b> the dots within 2 px (200 m) of <code>labels.tif</code> (60,988 known-fault pixels). All 37,654 champion dots lie inside d2.8. The champion has <b>0</b> dots within 2 px of the catalogue; d2.8 has 6,436 (14.6%). Within 300 m: 5.8% (champion) vs 19.5% (d2.8).</li>
<li><b>Owner-reported effect:</b> d2.8 0.2600 → champion 0.2778 (+0.0178). OWNER-REPORT.</li>
<li><b>The premise is not verified here:</b> the mechanism needs the organizer's hidden test to down-weight catalogue faults. The repo states this; DrivenData is unreachable from this sandbox (HTTP 000), so it cannot be checked today.</li>
<li><b>The repo holdout cannot see this mechanism.</b> The HIDE-RECOVER holdout gives the champion 0.0045, the lowest in the family, while random dots score 0.045–0.049 on the same test (two-seed control run). The holdout penalizes catalogue pruning, which is the effect the leaderboard may reward. Do not use it alone to pick a file.</li>
</ul></section>
<section class="alert"><h2>Portal error: "Predicted values must be in range [0, 1]"</h2>
<ul>
<li><b>Verified:</b> every finite value in every downloadable TIF is inside [0, 1] (scanned 31 files, 0 values outside range). No file has infinite values.</li>
<li><b>Verified:</b> five focus files (GEMSDOE24, 25, 27, 28, 31) and 18 of the 31 TIFs scanned contain NaN outside the footprint (7,111,787 pixels in each case; none inside). The owner-mirrored template <code>sample_submission.tif</code> has the same pattern (nodata = NaN, 7,111,787 NaN pixels outside its 5,167,373-pixel footprint).</li>
<li><b>Therefore:</b> NaN outside the footprint is the template's own convention. The portal's behaviour is <b>not established</b> here. The repo's statement that the official page allows NaN outside the footprint could not be re-read (DrivenData and NLR unreachable). Owner-reported scores for NaN files (e.g., 0.2708, 0.2600) suggest the portal accepted some of them, which conflicts with the error you saw. Unresolved.</li>
<li><b>Safe rule for any future file:</b> finite values everywhere, zero outside the footprint. That passes the strict check. But zero-filling an existing file gives the same predictions, which is a duplicate and not allowed as a unique submission.</li>
<li><b>To resolve:</b> send the exact file name and size you uploaded, plus the portal's error text. I can check those bytes against the strict check.</li>
</ul></section>
<section><h2>Estimate method</h2>
<ul>
<li><b>Existing files:</b> the only numbers are OWNER-REPORT scores. No organizer receipt ties any score to a file hash in this repo.</li>
<li><b>New files:</b> not estimable. The only projection is an analog from the 117-raster owner ledger, binned by SGMC-calibrated DTI (rank-association only, rho +0.40). Its top bin (&ge;0.10) has a lower median score (0.07) than 0.055–0.064 (0.23), so it is not monotonic and cannot be read as a score.</li>
</ul></section>
<section class="alert"><h2>Irregularities flagged for review</h2>
<p>Canonical numbering is the one in <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/arena/8d33bc2d-apartgemsdoe3/docs/research/session-20261031-e1-euler-review.md">the session review, section 8</a>. Legacy IDs used in the E1 run card: IR-E1-01 = IR-3, IR-E1-02 = IR-4.</p>
<ol>
<li><b>IR-1 Leaderboard values conflict.</b> Prompt: 0.4413 and 0.3195. Repo observations: 0.4437 (2026-10-26) and 0.4544 (2026-10-30). No live read was possible; none is an organizer receipt.</li>
<li><b>IR-2 GEMSDOE25 vs GEMSDOE30.</b> Not byte-identical (SHA-256 <code>91eae1ca…</code> vs <code>8cf893ea…</code>). Same positive dot mask; GEMSDOE30 is zero-filled. Earlier wording "byte-identical" is corrected.</li>
<li><b>IR-3 Uniqueness metric depends on registry density.</b> Dense lattice raster 13GEMSDOE (206,895 dots): 99.97% forward overlap from E1, 4.1% reverse. The literal 70% rule was kept, not waived. Owner decision needed on a density-corrected metric.</li>
<li><b>IR-4 HIDE-RECOVER holdout rewards catalogue-proximate dots.</b> Random dots score 0.045–0.049 against the champion's 0.0045. The gate is safe only because the SGMC-CAL non-regression gate also applies.</li>
<li><b>IR-5 NaN rule unverified.</b> The repo says the official page allows NaN outside the footprint; this could not be re-read here. The strict validator rejects NaN everywhere, which is stricter than the template.</li>
<li><b>IR-6 Owner NaN scores vs portal error.</b> NaN-containing files carry owner-reported scores, yet the user reported a range error. Unresolved; needs the file name and the exact portal text.</li>
<li><b>IR-7 Gate note cites DrivenData page 967.</b> Cited in <code>evidence/nine_site_verification_20261030.json</code>; not re-read this session.</li>
<li><b>IR-8 Lane not assigned.</b> The protocol's method paragraph is absent from the prompt. E1 was chosen from the repo's own shortlist, not from an assigned lane.</li>
<li><b>IR-9 Full registry not rerun.</b> The 2026-10-28 scan (784 unique rasters) is cited, not re-verified. Only the 131 registry rasters in the E1 uniqueness run were compared.</li>
<li><b>IR-10 SGMC proxy is non-monotonic.</b> Rank correlation with owner scores is +0.40 (n=117), but the top bin (&ge;0.10) has a lower median (0.07) than 0.055–0.064 (0.23). Use as a rank tool only.</li>
<li><b>IR-11 Nine-site association is n=9.</b> ρ = +0.95 (owner vs SGMC-CAL) and ρ = +1.00 (owner vs share beyond 1 km) come from one family of nine files. Not evidence of a general rule.</li>
<li><b>IR-12 Main-branch CTAs overstated.</b> Merged main showed "Download: YES" for H-GEO-1 and "OK TO DOWNLOAD ONLY" for H1 while the registry says <code>any_file_ok_to_submit=false</code>. Both files fail the literal uniqueness rule (7 of 131 each). Removed on this branch; the files remain for audit.</li>
<li><b>IR-13 H-GEO-1 card verdict "promote" conflicts with its own fields.</b> SGMC-CAL 0.0405 is below the champion 0.0641, and its lane check fails at 99.94% within 3 px of 13GEMSDOE. Its README line "UNIQUE vs all scored registry rasters (max 46.24%)" is not reproduced. Owner review of that card is needed.</li>
<li><b>IR-14 Evaluator labels differ.</b> E1 and H-GEO-1 use GEMSDOE32-HIDE-RECOVER-v3.0; H1 uses GEMSDOE32-HOLDOUT-v3-visible-gated with n=22,232. Not reconciled here; both labels are reported as recorded.</li>
</ol></section>
<section><h2>Limits and what is needed</h2>
<ul>
<li><b>Reachable from this sandbox:</b> github.com, codeload, api.github.com, pypi, npm.</li>
<li><b>Unreachable (HTTP 000, re-checked 2026-10-31):</b> drivendata.org (competition data, template, leaderboard, problem page), docs.nlr.gov (submission spec), usgs.gov, epsg.io, and the owner Pages sites (buffedlizard55-lab.github.io). The organizer template could not be authenticated, so all format checks use an owner mirror.</li>
<li><b>Needed to make progress:</b> (1) the organizer template and data, or the NLR spec text, to settle the NaN rule; (2) the exact failing file and portal error text; (3) an owner decision on the uniqueness metric (IR-3); (4) an assigned method lane; (5) a live leaderboard read from a machine that can reach DrivenData.</li>
</ul></section>
'''


def build_pages(root: Path = ROOT) -> dict[str, str]:
    status = json.loads((root / "registry/current_status.json").read_text())
    current_card = json.loads((root / status["current_run_card"]).read_text())
    current = status["current_candidate"]
    current_id = current["candidate_id"]
    current_hash = current["sha256"]
    audit = json.loads((root / "evidence/nine_site_best_files_audit.json").read_text())
    research = root / "docs/research/next-hypotheses-review-20261028.md"
    review = root / "docs/repo-review-current-session-2026-10-28.md"
    if not research.exists() or not review.exists():
        raise FileNotFoundError("Current review and hypothesis notes must exist before site build")

    sites = audit["sites"]
    top = max(sites, key=lambda row: row["published_score_OWNER_REPORT"])
    rows = []
    for item in sites:
        site = esc(item["site"])
        score = float(item["published_score_OWNER_REPORT"])
        site_pairings = []
        for pair in audit.get("pairwise", []):
            if pair["a"] == item["site"]:
                site_pairings.append((pair["b"], float(pair["a_dots_within_3px_of_b"]), abs(float(pair["spearman_footprint"]))))
            elif pair["b"] == item["site"]:
                site_pairings.append((pair["a"], float(pair["b_dots_within_3px_of_a"]), abs(float(pair["spearman_footprint"]))))
        peer, overlap, _ = max(site_pairings, key=lambda row: row[1])
        max_rho = max(row[2] for row in site_pairings)
        duplicate_status = f"NOT UNIQUE vs supplied nine: {overlap:.2%} within 3 px of {esc(peer)}; max |rho| {max_rho:.4f}; >70% gate FAIL"
        file_name = Path(str(item["file"])).name
        rows.append(
            "<tr>"
            f'<td><a href="https://github.com/buffedlizard55-lab/{site}">{site}</a></td>'
            f"<td><code>{esc(file_name)}</code></td>"
            f"<td>OWNER-REPORT {score:.4f}</td>"
            "<td>Not estimable</td>"
            f"<td>{duplicate_status}</td>"
            "<td><b>DO NOT DOWNLOAD TO SUBMIT</b>: owner reports it is already on the leaderboard, and it is not unique versus the other eight.</td></tr>"
        )
    table = (
        '<div class="scroll"><table><thead><tr><th>Site</th><th>File (already submitted)</th>'
        '<th>Reported score</th><th>New score estimate</th><th>Uniqueness vs these nine</th><th>Verdict</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
    )
    calib = calibration_summary(root)
    warning = (
        '<section class="alert"><strong>DO NOT SUBMIT — NOT YET OK TO SUBMIT.</strong> No file is OK to download or submit. H1 is research-only and fails literal uniqueness (7 of 131 flagged). '
        "No candidate has passed all required scientific, uniqueness, format, and selector gates. No weekly slot was used. "
        f"Current negative candidate {esc(current_id)}; SHA-256 <code>{esc(current_hash)}</code>; "
        f"submission name <code>{esc(current_card.get('submission_name', 'not recorded'))}</code>. "
        "The historical files are audit/research records only; this site does not authorize downloads.</section>"
    )
    # Additional exploratory artifact, kept separate from the current release record.
    # The byte-level format pass is not a uniqueness or submission authorization.
    wchd_card_path = root / "evidence/wchd_run_card.json"
    if wchd_card_path.is_file():
        wchd = json.loads(wchd_card_path.read_text(encoding="utf-8"))
        if wchd.get("verdict") != "negative" or wchd.get("ok_to_submit") is not False:
            raise ValueError("WCHD research artifact must remain fail-closed")
        artifact_path = str(wchd["artifact"])
        research_url = "https://github.com/apartanish22-droid/ApartGEMSDOE3/raw/main/" + artifact_path
        warning += (
            '<section class="alert"><h2>WCHD research artifact — DO NOT SUBMIT</h2>'
            '<p>Format checks pass against an owner-mirrored template, but its final dots fail the literal '
            'all-registry overlap rule (99.56% against the registered calibration lattice). '
            'The assigned lane was missing and the run exceeded protocol limits; the result is exploratory, not a score estimate.</p>'
            f'<p><a href="{esc(research_url)}">Download GeoTIFF for research only</a> · '
            f'<a href="{esc(repo_link("evidence/wchd_run_card.json"))}">Negative run card</a> · '
            f'<a href="{esc(repo_link("evidence/wchd_literal_recheck.json"))}">Format and overlap recheck</a></p>'
            f'<p>SHA-256 <code>{esc(wchd["raster_sha256"])}</code></p></section>'
        )
    artifact = current_card.get("artifacts", {}).get("primary_zeros_tif", current.get("artifact", ""))
    artifact_name = current_card.get("submission_name", "not recorded")
    holdout_data = current_card.get("holdout_dti") or {}
    holdout = holdout_data.get("primary_hide_and_recover", holdout_data)
    paired = holdout_data.get("paired_delta_vs_02778_champion")
    if paired:
        paired_note = (
            f"Paired delta vs 0.2778 incumbent: {float(paired['mean_boot_delta']):+.6f} "
            f"(95% CI {paired['ci95']}); this does not establish a positive improvement."
        )
    else:
        paired_note = "No paired same-evaluator comparison to the incumbent is recorded; improvement is not established."
    if current_id == "H-APART3-2-CTHG-DHC":
        current_registry_note = "This CTHG-DHC card reports registered-raster overlap examples of 75.90%, 72.25%, and 99.8035% within 3 px; its literal gate fails."
    else:
        current_registry_note = "For this current candidate, the full-registry surface and final-dot comparison was not run; off-catalogue masking is not a uniqueness pass."
    if current_card.get("scientific_integrity_gate", {}).get("issue"):
        science_note = esc(current_card["scientific_integrity_gate"]["issue"])
    else:
        science_note = "Feature-alone leakage canaries were not computed, and the assigned lane is absent; physical mimics remain unresolved."

    home = warning + '<section><h2>Start here</h2><p><b>No file is cleared to download or submit.</b> Read the <a href="executive-summary.html">executive summary</a> for the verified answer, the per-site table, and why the portal error occurs.</p></section>' + f'''<section><h2>Decision at a glance</h2>
<p>The highest result among these nine sites is <b>{esc(top['site'])}: OWNER-REPORT {float(top['published_score_OWNER_REPORT']):.4f}</b> for <code>{esc(top['leaderboard_name'])}</code>. This is an owner-supplied report, not an organizer receipt. It does not establish that the artifact's method caused the score or predict the score of a new raster.</p>
<p><a href="executive-summary.html">Open the executive summary</a> for the site-by-site comparison and exact upload checklist.</p>
<p>Current candidate record: <code>{esc(current_id)}</code>, file <code>{esc(artifact)}</code>, SHA-256 <code>{esc(current_hash)}</code>, submission name <code>{esc(artifact_name)}</code>. It is a negative research record; no download or upload is authorized. The associated literal-registry and scientific-integrity gates fail.</p></section>
<section><h2>What blocks a new result?</h2><ul><li>The assigned method paragraph is missing.</li><li>The raw 19-band raster was restored to ignored cache from a hash-pinned owner mirror on 2026-10-31, not an organizer-authenticated download; the prepared shared feature cache and full registry are not confirmed restored.</li><li>Historical candidate audits found uniqueness/scientific-integrity failures; format validation alone is insufficient.</li></ul><p class="muted">Latest review: <a href="repo-review-2026-10-31.md">three-pass repository review and nine-site summary</a> · <a href="release-status.html">release status</a> · <a href="review.html">repository review</a> · <a href="research.html">unrun research shortlist</a></p></section>'''

    latest_review = (
        '<section><h2>Latest repository review · 2026-10-31</h2>'
        '<p>Three-pass review: no new TIFF or score estimate is authorized. The per-site audit, ranked unrun hypotheses, blockers, source links, and verification results are in the '
        '<a href="repo-review-2026-10-31.md">current repository review</a> and its '
        f'<a href="{esc(repo_link("evidence/repo_review_20261031_run_card.json"))}">negative run card</a>.</p></section>'
    )
    exec_body = warning + DECISION_HTML_20261031 + latest_review + start_here_html(root) + candidate_under_review_html(root) + f'''<section><h2>Nine-site comparison</h2>
<p>All submitted-score entries below are <b>OWNER-REPORT</b> from the supplied/repository audit. None is organizer-confirmed here. The score estimate for a new submission is <b>not estimable</b>; a HOLDOUT-DTI result cannot be converted to a live score without a validated calibration study.</p>{table}
{calib}
<p>{esc(top['site'])} is the largest listed owner report ({float(top['published_score_OWNER_REPORT']):.4f}). Existing analysis says the reported nested pruning sequence is consistent with removing low-credit false-positive mass, but no hidden truth or receipt-linked evidence establishes causation. See <a href="{esc(repo_link('knowledge/03_why_02778_and_the_anatomy_of_the_family.md'))}">the evidence and limitations</a>.</p><p>There is no file currently OK to submit. The nine reported files are <b>NOT UNIQUE in this nine-site cohort</b> according to the repository overlap audit; scores remain OWNER-REPORT, not organizer receipts. {current_registry_note} Earlier `H-APART3-2-CTHG-DHC` (`apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif`) had recorded overlaps of 75.90%, 72.25%, and 99.8035% within 3 px and a Band 6 interpretation issue; its paired HOLDOUT-DTI delta versus the 0.2778 incumbent was +0.000571 (95% CI [-0.006306, +0.007311]), spanning zero. For the current candidate, HOLDOUT-DTI diagnostic is <b>{float(holdout.get('pooled_dti', 0.0)):.6f}</b> (evaluator <code>{esc(holdout.get('evaluator_version', 'not recorded'))}</code>, n={int(holdout.get('n_withheld_positives', 0))}, 95% CI {esc(holdout.get('ci95', []))}); it is not a leaderboard score projection. {paired_note} Scientific-integrity review: {science_note}</p><p>Current negative candidate: <code>{esc(current_id)}</code> · <code>{esc(artifact)}</code> · SHA-256 <code>{esc(current_hash)}</code>. Not authorized to download or submit; local format validity does not cure scientific or uniqueness failures.</p></section>
<section><h2>How to submit when a candidate is authorized</h2><ol><li>Only after the separate selector authorizes a slot, download the exact hash-verified GeoTIFF linked by the release page.</li><li>Open the correct <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS competition</a> and select <b>New submission</b>.</li><li>Choose the single-band GeoTIFF (or a ZIP containing exactly one GeoTIFF) that passed the release checklist. Confirm its CRS, shape, geotransform, and all predicted values in [0, 1].</li><li>Enter the submission name and a short note (140 characters maximum) recorded in the run card. Do not use an estimated score as the note.</li><li>Submit and retain the organizer's receipt. Record the exact file SHA-256 and the receipt's score as <b>ORGANIZER-CONFIRMED</b>.</li></ol><p><b>Current decision: no file is authorized for submission.</b> Exact portal acceptance cannot be guaranteed by a local validator.</p></section>'''

    release = warning + f'''<section><h2>Current release gates</h2><p>{esc(status.get('headline', 'DO NOT SUBMIT'))}</p>
<ul><li>Method lane explicitly assigned: no.</li><li>New surface/final-dot registry comparisons: not run this review.</li><li>Historical CSHD literal uniqueness: failed; format pass is against an owner mirror only.</li><li>Organizer-authenticated template: not available in this checkout.</li><li>Weekly slot selected or used: no.</li></ul><p>Machine-readable status: <a href="{esc(repo_link('registry/current_status.json'))}">current status JSON</a> · <a href="{esc(repo_link('evidence/session_review_20261028.json'))}">current review card</a> · <a href="{esc(repo_link('run_card.json'))}">historical candidate run card</a>.</p></section>'''

    instructions = warning + '''<section><h2>Submission checklist</h2><ol><li>Do not submit until a candidate beats the current holdout incumbent on the agreed spatially blocked, buffered hide-and-recover evaluator, with a paired 95% CI supporting the improvement.</li><li>Run each feature-alone leakage canary; AUC above 0.90 is presumed leakage until resolved.</li><li>Pass the pre-placement surface correlation and post-placement dot overlap gates against every registry raster; log a duplicate and stop on a threshold breach.</li><li>Pass automated single-band GeoTIFF validation against the competition template: matching CRS, shape, transform, finite values in [0,1] across the full array.</li><li>Obtain explicit separate selector authorization within the current weekly slot cap.</li><li>Download the exact authorized file, submit it on the competition page, and save the organizer receipt.</li></ol><p>These checks are independent; a format pass does not override a holdout, uniqueness, scientific-integrity, or selector failure.</p></section>
<section><h2>Submission fields</h2><p>The submission-form text supplied in this project says a single-band GeoTIFF or a ZIP containing one GeoTIFF is accepted. Confirm the live rules on the official competition page before upload. Use the submission name and a concise comment stored in that candidate's run card. The local validator checks file structure/range, not portal account, slot quota, score, or scientific validity.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Competition data / format page</a> (login may be required).</p></section>'''

    research_body = warning + f'''<section><h2>Research status</h2><p>There was no new experiment in this review. The assigned method paragraph was not identifiable, and the predictor stack and full raster registry are missing. The shortlist is preregisterable research, not validated performance or a submission recommendation.</p><p><a href="research/next-hypotheses-review-20261028.md">Read the ranked four-hypothesis shortlist</a> · <a href="{esc(repo_link('knowledge/03_why_02778_and_the_anatomy_of_the_family.md'))}">Why the 0.2778 owner report does not imply a score projection</a>.</p><h3>Next gates</h3><ol><li>Resolve the lane and restore hash-checked data.</li><li>Run feature-alone canaries.</li><li>Use visible-only buffered segment holdout and exact masking.</li><li>Run literal all-registry checks before and after placement.</li><li>Keep weekly-slot selection separate.</li></ol></section>'''

    hypotheses_body = warning + '''<section><h2>Unrun candidates</h2><p>The current shortlist ranks four in-band hypotheses by qualitative expected utility and cost, names non-fault mimics, and documents repository overlaps. These are not numeric DTI estimates.</p><ol><li>Buried sediment-cover thickness ridge with a surface-quiescence gate (top research priority; related to unvalidated H61-1).</li><li>Directional semivariogram anisotropy of potential-field residuals.</li><li>Signed cross-edge magnetic–gravity offset persistence.</li><li>Paired signed cross-front topographic profile residual.</li></ol><p><a href="research/next-hypotheses-review-20261028.md">Full proposal, layer names, caveats, and cost ranking</a>.</p></section>'''

    leaderboard = warning + f'''<section><h2>Scope and evidence classes</h2><p>This page audits the nine supplied site claims; it is not a live leaderboard feed. Best listed result: {esc(top['site'])}, OWNER-REPORT {float(top['published_score_OWNER_REPORT']):.4f}. No new score estimate is available.</p>{table}<p>Official public leaderboard: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData leaderboard</a>. It was not fetched during this review, so no current rank is asserted.</p></section>'''

    review_body = warning + f'''<section><h2>Current review — 2026-10-31</h2><p><a href="repo-review-2026-10-31.md">Read the current three-pass repository review</a> and <a href="{esc(repo_link('evidence/repo_review_20261031_run_card.json'))}">machine-readable negative run card</a>. The README remains the persistent project brief and first-read requirement.</p><p>Reproduced checks: <b>119 passed, 2 skipped</b> after restoring two hash-pinned owner-mirror inputs; <code>scripts/check_release_status.py</code> passed. No new experiment or TIFF was generated. The assigned method lane, full training feature raster/cache, and complete registry remain unavailable in this checkout; no new holdout or candidate uniqueness experiment was run.</p><p>All supplied focus-site score claims remain OWNER-REPORT, not organizer receipts. No file is authorized for competition download/submission. Review the <a href="{esc(repo_link('evidence/nine_site_best_files_audit.json'))}">nine-site byte/overlap audit</a> and <a href="{esc(repo_link('evidence/irregularities_ledger.json'))}">irregularities ledger</a>.</p></section>'''

    sources_body = warning + f'''<section><h2>Official review pointers</h2><ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition overview</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">data/format page</a>, and <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a>.</li><li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference solution</a>.</li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a>, <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a>, <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a>, and <a href="https://gdr.openei.org/submissions/1391">GDR submission 1391</a>.</li><li><a href="https://epsg.io/32611">EPSG:32611</a>.</li></ul><p>These are source pointers for review. Current source contents/reachability were not revalidated in this session. Provenance and prior access notes are in <a href="{esc(repo_link('registry/sources.json'))}">registry/sources.json</a>.</p></section>'''

    docs = {
        "index.html": page("Overview", home),
        "executive-summary.html": page("Executive summary", exec_body),
        "release-status.html": page("Release status", release),
        "submissions.html": page("How to submit", instructions),
        "research.html": page("Research status", research_body),
        "hypotheses.html": page("Research hypotheses", hypotheses_body),
        "leaderboard.html": page("Score audit", leaderboard),
        "review.html": page("Repository review", review_body),
        "sources.html": page("Sources", sources_body),
        "executive-summary/index.html": page(
            "Executive summary",
            exec_body.replace('href="downloads/', 'href="../downloads/').replace(
                'href="../knowledge/', 'href="../../knowledge/'
            ).replace('href="repo-review-2026-10-31.md"', 'href="../repo-review-2026-10-31.md"'),
            prefix="../",
        ),
    }
    return docs


def build_page(source: dict, audit: dict, status: dict) -> str:
    """Compatibility API for the executive summary; inputs are repository audit records."""
    del source, audit, status  # build_pages loads the same versioned records from ROOT.
    return build_pages(ROOT)["executive-summary.html"]


def main() -> None:
    sync_status_artifacts()
    pages = build_pages()
    for relative, content in pages.items():
        target = ROOT / "docs" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    status = json.loads((ROOT / "registry/current_status.json").read_text())
    current = status["current_candidate"]
    current_card = json.loads((ROOT / status["current_run_card"]).read_text())
    current_file = current_card.get("artifacts", {}).get("primary_zeros_tif", "")
    current_name = current_card.get("submission_name", "not recorded")
    gateway = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=docs/index.html">'
        '<title>ApartGEMSDOE3 — DO NOT SUBMIT</title></head><body>'
        '<h1>DO NOT SUBMIT</h1><p>Current negative candidate '
        + esc(current["candidate_id"]) + ' · SHA-256 <code>' + esc(current["sha256"])
        + '</code> · file <code>' + esc(current_file) + '</code> · submission name <code>'
        + esc(current_name) + '</code>.</p><p><a href="docs/index.html">Open the fail-closed review portal</a>.'
        '</p></body></html>\n'
    )
    (ROOT / "index.html").write_text(gateway, encoding="utf-8")
    print(f"Built {len(pages)} distinct fail-closed pages and the root gateway")


if __name__ == "__main__":
    main()
