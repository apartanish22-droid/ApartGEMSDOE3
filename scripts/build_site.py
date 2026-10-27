#!/usr/bin/env python3
"""Render the static historical scorecard from the reproducible JSON audit."""
from __future__ import annotations

import argparse
import csv
import html
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def e(value):
    return html.escape(str(value), quote=True)


def render(template: str, values: dict) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    if "{{" in template or "}}" in template:
        raise ValueError("unresolved template variable")
    return template


def raw_link(row):
    return row["source"].replace("/blob/", "/raw/", 1)


def outputs():
    audit = json.loads((ROOT / "evidence/prior_audit.json").read_text())
    history = audit["historic"]
    reviews = json.loads((ROOT / "registry/site_review.json").read_text())
    parallel_audit = json.loads((ROOT / "evidence/mrcj_audit.json").read_text())
    parallel_card = json.loads((ROOT / "evidence/run_card.json").read_text())
    if (parallel_card["verdict"] != "negative" or parallel_card["ok_to_submit"] is not False
            or parallel_card["raster_sha256"] != parallel_audit["candidate_sha256"]
            or not parallel_audit["duplicate_by_overlap"]):
        raise ValueError("parallel MRCJ audit and fail-closed decision disagree")
    if len(history) != 9 or set(reviews["sites"]) != set(history):
        raise ValueError("expected matching reviews for nine explicitly named historical references")
    idx = (ROOT / "site_templates/index.html").read_text()
    sub = (ROOT / "site_templates/site.html").read_text()
    rows = []
    result = {}
    stream = io.StringIO(newline="")
    columns = ["site", "historical_archive_filename", "historical_archive_source", "sha256",
               "historical_user_report_unverified", "estimated_organizer_score", "worst_other_site", "overlap_within_3px",
               "in_footprint_finite_in_range", "strict_all_cells_finite_in_range", "unique_vs_named_sites", "submit"]
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for site, row in history.items():
        name = row["filename"]
        source, raw = row["source"], raw_link(row)
        uniq = row["nine_site_uniqueness"]
        if not uniq["complete_against_eight_named_history_files"] or not uniq["duplicate_against_any"]:
            raise ValueError(f"unexpected or incomplete historical uniqueness result: {site}")
        overlap = f"{uniq['worst_overlap_within_3px'] * 100:.2f}%"
        score = f"{row['claimed_score']:.4f}"
        diag = row["format_diagnostics"]
        inside = "YES" if diag["inside_footprint_finite_and_in_range"] else "NO"
        whole = "YES" if diag["strict_all_finite_and_in_range"] else "NO"
        site_review = reviews["sites"][site]
        rows.append(
            f'<tr><td><strong><a href="docs/sites/{e(site)}.html">{e(site)}</a></strong>'
            f'<span class="subtext">Site brief →</span></td><td><a class="file-link" href="{e(raw)}">{e(name)}</a>'
            f'<span class="subtext">Research archive only · do not submit</span></td>'
            f'<td><strong>{score}</strong><span class="subtext">USER-REPORTED<br>unverified</span></td>'
            f'<td>Unavailable<span class="subtext">No validated forecast</span></td>'
            f'<td>Inside: {inside}<span class="subtext">All cells: {whole}</span></td>'
            f'<td><span class="status-no">NO</span><span class="subtext">{overlap} vs {e(uniq["worst_reference"])}</span></td>'
            f'<td><span class="status-no">NO</span></td></tr>'
        )
        values = {"SITE": e(site), "SCORE": score, "OVERLAP": overlap,
                  "WORST": e(uniq["worst_reference"]), "FILE": e(name), "SHA": e(row["sha256"]),
                  "RAW_URL": e(raw), "SOURCE_URL": e(source), "SITE_URL": e(site_review["url"]),
                  "CURRENT_REVIEW": e(site_review["current_review"]),
                  "HISTORICAL_REVIEW": e(site_review["historical_review"]),
                  "REVIEW_TIME": e(reviews["observed_utc"]),
                  "DOTS": f"{diag['positive_footprint_pixels']:,}",
                  "NONFINITE": f"{diag['nonfinite_all_pixels']:,}",
                  "INSIDE_RANGE": inside, "WHOLE_RANGE": whole}
        result[ROOT / f"docs/sites/{site}.html"] = render(sub, values)
        writer.writerow({"site": site, "historical_archive_filename": name,
                         "historical_archive_source": source, "sha256": row["sha256"],
                         "historical_user_report_unverified": score, "estimated_organizer_score": "",
                         "worst_other_site": uniq["worst_reference"],
                         "overlap_within_3px": f"{uniq['worst_overlap_within_3px']:.8f}",
                         "in_footprint_finite_in_range": inside, "strict_all_cells_finite_in_range": whole,
                         "unique_vs_named_sites": "NO", "submit": "NO"})
    holdout = parallel_card["holdout_dti"]
    ci = holdout["ci95"]["interval"]
    mrcj_rows = parallel_audit["historical_comparisons"]
    if len(mrcj_rows) != 9:
        raise ValueError("MRCJ nine-file comparison is incomplete")
    result[ROOT / "index.html"] = render(idx, {"TABLE_ROWS": "\n".join(rows),
        "AUDIT_TIME": "Historical raster audit: " + e(audit["observed_utc"]),
        "MRCJ_FILE": e(parallel_card["submission_name"]),
        "MRCJ_SHA": e(parallel_audit["candidate_sha256"]),
        "MRCJ_DOTS": f"{parallel_audit['candidate_in_footprint_dots']:,}",
        "MRCJ_LATTICE": f"{parallel_audit['three_pixel_overlap_fraction'] * 100:.2f}%",
        "MRCJ_NINE": f"{max(r['candidate_dot_overlap_within_3px'] for r in mrcj_rows) * 100:.2f}%",
        "MRCJ_DTI": f"{holdout['dti']:.5f}",
        "MRCJ_CI": f"[{ci[0]:.5f}, {ci[1]:.5f}]",
        "MRCJ_WITHHELD": f"{holdout['n_withheld_positive_pixels']:,}",
        "MRCJ_EVALUATOR": e(holdout["evaluator_version"])})
    result[ROOT / "docs/data/site_scorecard.csv"] = stream.getvalue()
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    bad = []
    for path, content in outputs().items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                bad.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if bad:
        print("Generated site is out of date: " + ", ".join(bad), file=sys.stderr)
        return 1
    print("Site is up to date." if args.check else "Rendered static scorecard and nine site briefs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
