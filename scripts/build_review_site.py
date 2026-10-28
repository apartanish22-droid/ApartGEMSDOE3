#!/usr/bin/env python3
"""Build a fail-closed research portal from current status and archived audits."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def esc(value):
    return html.escape(str(value), quote=True)


def _load_current_card(status: dict) -> tuple[dict, Path]:
    """Resolve the current candidate card from the status record, not stale root card."""
    candidate = status.get("current_candidate") or {}
    sources = str(candidate.get("source", "")).split(";")
    card_path = next(
        (ROOT / item.strip() for item in sources
         if item.strip().startswith("evidence/") and item.strip().endswith("_run_card.json")
         and (ROOT / item.strip()).is_file()),
        None,
    )
    if card_path is None:
        card_path = ROOT / "run_card.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    artifact = candidate.get("artifact")
    if candidate.get("verdict") != "negative" or candidate.get("ok_to_submit") is not False:
        raise SystemExit("Review portal requires a negative, non-authorized current candidate")
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise SystemExit(f"Current candidate card is not fail-closed: {card_path.relative_to(ROOT)}")
    if artifact != card.get("artifacts", {}).get("primary_zeros_tif"):
        raise SystemExit("Current status artifact does not match its candidate run card")
    if candidate.get("sha256") != card.get("raster_sha256"):
        raise SystemExit("Current status SHA-256 does not match its candidate run card")
    return card, card_path


def main():
    status = json.loads((ROOT / "registry/current_status.json").read_text(encoding="utf-8"))
    card, card_path = _load_current_card(status)
    candidate_status = status["current_candidate"]
    audit = json.loads((ROOT / "evidence/nine_site_best_files_audit.json").read_text(encoding="utf-8"))
    rows = []
    for item in audit["sites"]:
        site = item["site"]
        rows.append(
            f'<tr><td><a href="https://buffedlizard55-lab.github.io/{esc(site)}/">{esc(site)}</a></td>'
            f'<td><code>{esc(item["leaderboard_name"])}</code></td>'
            f'<td>OWNER-REPORT {item["published_score_OWNER_REPORT"]:.4f}</td>'
            '<td>Not estimable</td><td>Historical; not authorized</td></tr>'
        )

    relative_artifact = candidate_status["artifact"]
    filename = Path(relative_artifact).name
    download_url = (
        "https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/" + relative_artifact
    )
    primary = card["holdout_dti"]["primary_hide_and_recover"]
    score = primary.get("pooled_dti", primary.get("dti"))
    ci_low, ci_high = primary["ci95"]
    n_withheld = primary["n_withheld_positives"]
    evaluator = primary["evaluator_version"]
    uniqueness = card["correlation_and_overlap_vs_registry"]
    duplicate = card["duplicate_gate_failure"]
    lattice = uniqueness["literal_5px_calibration_lattice_probe"]["within_3px_fraction"]
    top_overlap = duplicate["overlap_examples"][0]
    top_overlap_pct = top_overlap["fraction"] * 100
    science = card["scientific_integrity_gate"]
    note = card.get("submission_note", "")
    name = card.get("submission_name", "Not assigned")
    report_url = "https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/docs/repo-review-session-2026-10-28.md"
    card_url = "https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/" + card_path.relative_to(ROOT).as_posix()
    ci_text = f"{score:.6f} [{ci_low:.6f}, {ci_high:.6f}]"
    body = f'''<header><div class="wrap"><p class="eyebrow">APARTGEMSDOE3 · RESEARCH REVIEW</p><h1>Executive summary</h1>
    <div class="alert"><strong>DO NOT SUBMIT — no candidate has passed all required gates.</strong><p>The current research artifact is available for audit only. No weekly slot was used. A leaderboard-score estimate is not available.</p></div></div></header>
    <main class="wrap"><section><h2>Latest research artifact — {esc(card.get("candidate_id", "candidate"))}</h2><p><a href="{esc(download_url)}">Download {esc(filename)} for audit only</a> · SHA-256 <code>{esc(card["raster_sha256"])}</code></p>
    <p><strong>Submission decision: DO NOT UPLOAD.</strong> Candidate name <code>{esc(name)}</code>; suggested note <code>{esc(note)}</code>. These are metadata for auditing only, not authorization.</p>
    <p><strong>HOLDOUT-DTI</strong>, {esc(evaluator)}, {n_withheld:,} withheld positives, 95% CI: <code>{ci_text}</code>. This is a local proxy metric, not an organizer score or a live-score projection. No leaderboard estimate is defensible.</p>
    <p><strong>Uniqueness gate fails.</strong> Surface max absolute Spearman is {uniqueness["max_abs_surface_spearman"]:.6f} across {uniqueness["n_unique_rasters_checked"]} registry rasters, but final dots exceed the literal 70% limit: {top_overlap_pct:.4f}% overlap with {esc(top_overlap["raster"])} and {lattice * 100:.4f}% with the registered calibration lattice. The prompt allows no lattice or density exemption.</p>
    <p><strong>Scientific-integrity gate fails.</strong> {esc(science["issue"])} The artifact is preserved as a negative research result; its mechanism is not cleared for scientific promotion. The lane paragraph is also missing and the total experiment/time accounting is unreconciled.</p>
    <p>The strict local GeoTIFF checker passes for single band, finite values in [0,1], CRS, shape and transform against a hash-pinned owner mirror. This is only format validation; the mirror is not organizer-authenticated. See the <a href="{esc(card_url)}">current candidate run card</a> and <a href="{esc(report_url)}">independent repo review</a>.</p></section>
    <section><h2>Nine-site comparison</h2><p>These are owner-reported historical scores from the supplied focus-site audit, not organizer receipts or current leaderboard estimates. Files are for learning only; none is recommended for resubmission. The new candidate must be compared against the full applicable registry.</p>
    <div class="scroll"><table><thead><tr><th>Site</th><th>Reported best submission</th><th>Reported score</th><th>New submission estimate</th><th>Decision</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
    <p>GEMSDOE32 is the highest result in this supplied list: <code>h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros</code>, OWNER-REPORT 0.2778. Its score does not establish why it scored well, and does not support a projected result for a different raster. Read the <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/knowledge/03_why_02778_and_the_anatomy_of_the_family.md">analysis and limitations</a>.</p></section>
    <section><h2>How to submit after authorization</h2><ol><li>Use only a fresh, preregistered candidate in the assigned lane. Run the shared buffered segment holdout and each-feature leakage canary.</li><li>Require a better comparable HOLDOUT-DTI than the incumbent, a passing pre-placement and final-dot literal registry check, a verified scientific feature map, and exact-byte GeoTIFF validation.</li><li>Then—and only then—obtain the separate weekly-slot selector decision. Download the exact hash-verified GeoTIFF, open the correct <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition</a>, attach the short recorded note, submit, and retain the organizer receipt.</li></ol><p>No upload is authorized today. Local validation cannot guarantee portal acceptance.</p></section>
    <section><h2>Review and sources</h2><p>The referenced single-method lane paragraph was not included. The full feature stack is not cached in this checkout; competition files are login-walled. Some mirrored data and site scores are owner-reported, not organizer-authenticated. See the review for prioritized blockers and next actions.</p>
    <p><a href="{esc(report_url)}">Repository review</a> · <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/docs/research/next-hypotheses-20261028.md">Research proposals</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference solution</a> · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> · <a href="https://gbcge.org/current-projects/ingenious/">DOE INGENIOUS</a></p></section></main>'''
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GEMS research · release review</title><style>body{margin:0;background:#0c1423;color:#e8edf7;font:16px/1.6 system-ui,sans-serif} .wrap{max-width:1100px;margin:auto;padding:24px}header{background:#111f35}h1{font-size:2.3rem;margin:.2em 0}h2{margin-top:0}section{background:#142238;border:1px solid #30415c;border-radius:12px;margin:20px 0;padding:24px}.alert{padding:18px;background:#4c2025;border:1px solid #f88;border-radius:8px}.eyebrow{color:#77d0ed;letter-spacing:.12em}a{color:#82d9fa}code{overflow-wrap:anywhere;color:#fff}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:750px}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #40516b}</style></head><body>''' + body + '</body></html>\n'
    for rel in ['index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/executive-summary/index.html', 'docs/release-status.html', 'docs/submissions.html', 'docs/research.html', 'docs/hypotheses.html', 'docs/leaderboard.html', 'docs/review.html', 'docs/sources.html']:
        (ROOT / rel).write_text(page, encoding="utf-8")

    # Keep machine-readable site data on the same current candidate as the UI.
    (ROOT / "docs/data/latest-run-card.json").write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    refreshed_audit = json.loads((ROOT / "evidence/nine_site_refreshed_audit_20261028.json").read_text(encoding="utf-8"))
    experiments = json.loads((ROOT / "evidence/apart3_cthg_dhc_experiments.json").read_text(encoding="utf-8"))
    site_data = {
        "run_card": card,
        "nine_site_audit": refreshed_audit,
        "experiments_summary": experiments["experiments"],
    }
    (ROOT / "docs/assets/site-data.json").write_text(json.dumps(site_data, indent=2) + "\n", encoding="utf-8")

    # Repair the stale feed pointer without rewriting unrelated historical entries.
    feed_path = ROOT / "docs/data/feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    feed["current_status"]["single_source_of_truth"] = (
        "registry/current_status.json and docs/data/latest-run-card.json identify the latest "
        "candidate; its evidence card is " + card_path.relative_to(ROOT).as_posix() + ". "
        "Root run_card.json is a separate historical CSHD card and is not the current candidate."
    )
    feed["current_candidate"]["run_card"] = card_path.relative_to(ROOT).as_posix()
    feed_path.write_text(json.dumps(feed, indent=1, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Built fail-closed review portal and current machine-readable feed from {card_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
