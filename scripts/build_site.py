#!/usr/bin/env python3
"""Build static GitHub Pages from the frozen, read-only forensic evidence."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render() -> dict[str, str]:
    manifest = json.loads((ROOT / "registry/focus_sites.json").read_text())
    audit = json.loads((ROOT / "evidence/historical_audit.json").read_text())
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    peer = json.loads((ROOT / "evidence/peer_reference_audit.json").read_text())
    parallel = json.loads((ROOT / "evidence/parallel_mrcj_audit.json").read_text())
    if (len(manifest["sites"]) != 9 or card.get("ok_to_submit") is not False or card.get("verdict") != "negative"
            or card.get("raster_sha256") != parallel["raster"]["sha256"] or card.get("weekly_slots_used_in_this_review") != 0
            or parallel.get("ok_to_submit") is not False or not parallel["registered_lattice"]["duplicate_under_literal_rule"]):
        raise ValueError("Static blocked-status site needs nine sites, a lattice failure, and a negative run card")
    if peer.get("ok_to_submit") is not False or peer.get("new_raster") is not False or peer.get("literal_lattice_duplicate") is not True:
        raise ValueError("Current research copy requires the peer reference to remain blocked")
    if audit.get("submission_authorized") is not False or audit.get("new_rasters_generated") != 0:
        raise ValueError("Audit status is not the expected no-submission snapshot")
    rows = []
    for source in manifest["sites"]:
        artifact = audit["artifacts"][source["site"]]
        if (source["git_blob"] != artifact["git_blob"] or artifact["estimated_organizer_score"] is not None
                or source["historical_value"] != artifact["historical_user_reported_value_unverified"]
                or artifact.get("ok_to_submit") is not False):
            raise ValueError("Manifest/audit mismatch, unverified score forecast, or unexpected authorization")
        if artifact["unique_vs_eight_historical_rasters"] is not False:
            raise ValueError("Current site copy assumes all nine historical examples failed uniqueness")
        overlap = artifact["highest_historical_overlap"]
        esc = lambda s: html.escape(str(s), quote=True)
        rows.append(
            "<tr>"
            f'<td><a class="site-name" href="{esc(source["site_url"])}">{esc(source["site"])} ↗</a>'
            f'<a class="artifact" href="{esc(source["source_url"])}">{esc(artifact["file"])} ↗</a>'
            '<span class="small">Historical comparison only</span></td>'
            f'<td><strong>{esc(source["historical_value"])}</strong><span class="claim">USER-REPORTED / UNVERIFIED</span></td>'
            '<td>Not estimable</td>'
            f'<td><span class="bad">NO</span><br><span class="small">{overlap["fraction"] * 100:.2f}% within 3 px of {esc(overlap["reference"])}</span></td>'
            '<td><span class="bad">NO</span><br><span class="small">Historical file; do not submit</span></td>'
            "</tr>"
        )
    # Keep peer claims and the evidence timestamp tied to checked-in evidence;
    # neither is a newly measured score or a live feed.
    holdout = peer["recorded_holdout_not_replayed"]
    prior = parallel["recorded_holdout_not_replayed"]
    if any(h["label"] != "HOLDOUT-DTI" or len(h["ci95"]) != 2 for h in (holdout, prior)):
        raise ValueError("Research copy requires labelled holdouts with CI")
    replacements = {
        "{{TABLE_ROWS}}": "\n".join(rows),
        "{{AUDIT_TIME}}": html.escape(audit["generated_utc"]),
        "{{PEER_DTI}}": f'{holdout["value"]:.6f}',
        "{{PEER_EVALUATOR}}": html.escape(holdout["evaluator_version"]),
        "{{PEER_POSITIVES}}": f'{holdout["withheld_positive_pixels"]:,}',
        "{{PEER_CI_LOW}}": f'{holdout["ci95"][0]:.5f}',
        "{{PEER_CI_HIGH}}": f'{holdout["ci95"][1]:.5f}',
        "{{PEER_NINE_OVERLAP}}": f'{100 * peer["maximum_vs_historical_nine"]["candidate_within_3px_fraction"]:.2f}',
        "{{PEER_LATTICE_OVERLAP}}": f'{100 * peer["candidate_within_3px_of_lattice"]:.2f}',
        "{{PEER_FILE_URL}}": html.escape(peer["raster"]["source"], quote=True),
        "{{PAR_FILE}}": html.escape(parallel["raster"]["file"]),
        "{{PAR_SHA}}": html.escape(parallel["raster"]["sha256"]),
        "{{PAR_DOTS}}": f'{parallel["raster"]["dots"]:,}',
        "{{PAR_LATTICE_OVERLAP}}": f'{100 * parallel["registered_lattice"]["candidate_within_3px_fraction"]:.2f}',
        "{{PAR_DTI}}": f'{prior["value"]:.6f}',
        "{{PAR_EVALUATOR}}": html.escape(prior["evaluator_version"]),
        "{{PAR_POSITIVES}}": f'{prior["withheld_positive_pixels"]:,}',
        "{{PAR_CI_LOW}}": f'{prior["ci95"][0]:.5f}',
        "{{PAR_CI_HIGH}}": f'{prior["ci95"][1]:.5f}',
    }
    output = {}
    for name in ("index.html", "executive-summary.html", "research.html"):
        text = (ROOT / "site_templates" / name).read_text()
        for key, value in replacements.items():
            text = text.replace(key, value)
        if "{{" in text or "}}" in text:
            raise ValueError(f"Unresolved site placeholder in {name}")
        output[name] = text
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if checked-in pages differ from templates/evidence")
    args = parser.parse_args()
    for path, text in render().items():
        out = ROOT / path
        if args.check:
            if not out.is_file() or out.read_text() != text:
                raise SystemExit(f"Stale page: {out}; run python scripts/build_site.py")
        else:
            out.write_text(text)
            print(f"Built {out}")


if __name__ == "__main__":
    main()
