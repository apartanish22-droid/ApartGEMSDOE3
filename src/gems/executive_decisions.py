"""Conservative nine-site packet; never selects or authorizes a weekly slot."""

from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path
from typing import Any

from .validator import sha256_file

SITES = tuple(f"GEMSDOE{n}" for n in (24, 25, 27, 28, 30, 31, 32, 33, 36))
CLAIMS = "registry/owner_reported_scores_2026-10-26.json"


def build_decisions(root: Path, current: dict[str, Any]) -> dict[str, Any]:
    """Combine the verified current audit with explicitly unverified owner claims."""
    root = Path(root)
    claims = json.loads((root / CLAIMS).read_text(encoding="utf-8"))
    if set(claims.get("sites", {})) != set(SITES):
        raise ValueError("Nine-site claim inventory must match the requested sites exactly")
    if current.get("ok_to_submit") is not False or current.get("verdict") != "negative":
        raise ValueError("Review packet cannot authorize submission")
    name = current.get("submission_name")
    if not isinstance(name, str) or Path(name).name != name or not name.endswith("-zeros.tif"):
        raise ValueError("Unsafe research filename")
    artifact = root / "docs/downloads" / name
    if not artifact.is_file() or sha256_file(artifact) != current.get("raster_sha256"):
        raise ValueError("Research download differs from reviewed bytes")

    rho_by_site = current.get("surface_spearman_vs_focus_registry", {})
    overlap_by_site = current.get("final_dot_overlap_within_3px_vs_focus_registry", {})
    holdout = current.get("holdout_dti", {})
    holdout_packet = {
        "label": holdout.get("label"),
        "dti": holdout.get("value"),
        "evaluator_version": holdout.get("evaluator_version"),
        "n_withheld_positive_pixels": holdout.get("withheld_positive_count"),
        "ci95": {"level": 0.95, "interval": holdout.get("ci_95")},
        "provenance": holdout.get("provenance"),
        "interpretation": holdout.get("interpretation"),
    }
    rows = []
    for site in SITES:
        entries = claims["sites"][site]
        if not entries:
            raise ValueError(f"Missing historical claims for {site}")
        for entry in entries:
            value = entry.get("owner_reported")
            if (
                not isinstance(entry.get("name"), str)
                or not entry["name"]
                or type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0 <= value <= 1
                or not isinstance(entry.get("source_url"), str)
            ):
                raise ValueError(f"Malformed owner-reported reference for {site}")
        best = max(entries, key=lambda entry: entry["owner_reported"])
        rho = rho_by_site.get(site)
        overlap = overlap_by_site.get(site)
        if type(rho) not in (float, int) or type(overlap) not in (float, int):
            uniqueness = "NOT ESTABLISHED: exact raster audit missing"
        elif abs(rho) <= 0.90 and overlap <= 0.70:
            uniqueness = f"PASS vs tracked raster only: Spearman {rho:.6f}; candidate-dot overlap <=3px {overlap:.2%}"
        else:
            uniqueness = f"FAIL vs tracked raster: Spearman {rho:.6f}; candidate-dot overlap <=3px {overlap:.2%}"
        rows.append({
            "site": site,
            "source_url": best["source_url"],
            "historical_reference": best["name"],
            "historical_claim": {
                "label": "UNVERIFIED-OWNER-REPORT",
                "value": best["owner_reported"],
                "source": CLAIMS,
            },
            "research_download": name,
            "holdout": holdout_packet,
            "leaderboard_estimate": None,
            "organizer_confirmed_score": None,
            "surface_spearman": rho,
            "final_dot_overlap_within_3px": overlap,
            "uniqueness": uniqueness,
            "ok_to_submit": False,
            "decision": "DO_NOT_SUBMIT",
        })
    return {
        "schema_version": "nine-site-decisions-v2",
        "scope": "Current exact-file review plus user-supplied owner claims; local comparison is limited to nine tracked rasters, no cross-site selection",
        "claims_provenance": claims.get("provenance"),
        "claims_sha256": sha256_file(root / CLAIMS),
        "leaderboard_estimate_method": "Unavailable: no independently calibrated paired organizer receipts",
        "rows": rows,
        "ok_to_submit": False,
        "verdict": "negative",
    }


def render_decisions(packet: dict[str, Any]) -> str:
    e = lambda value: escape(str(value), quote=True)  # noqa: E731
    rows = []
    for row in packet["rows"]:
        name, holdout = row["research_download"], row["holdout"]
        download = (
            f'<a href="downloads/{e(name)}" download="{e(name)}">{e(name)}</a>'
            "<br>Research only; DO NOT SUBMIT"
        )
        metric = "Not available"
        if holdout.get("label") == "HOLDOUT-DTI" and holdout.get("ci95", {}).get("interval"):
            low, high = holdout["ci95"]["interval"]
            metric = (
                f"HOLDOUT-DTI {holdout['dti']:.5f}; 95% CI [{low:.5f}, {high:.5f}]; "
                f"{e(holdout['evaluator_version'])}; "
                f"{holdout['n_withheld_positive_pixels']:,} withheld positives. Recorded, not replayed."
            )
        claim = row["historical_claim"]
        rows.append(
            f'<tr><th scope="row"><a href="{e(row["source_url"])}">{e(row["site"])}</a></th>'
            f"<td><code>{e(row['historical_reference'])}</code><br>"
            f"{e(claim['label'])}: {claim['value']:.4f}</td>"
            f"<td>{download}</td><td>{metric}</td>"
            f"<td>Not estimable</td><td>{e(row['uniqueness'])}<br>"
            "<strong>SUBMIT NO</strong></td></tr>"
        )
    return (
        '<section class="card" id="nine-site-download-decisions">'
        "<h2>Nine-site download and submission decisions</h2>"
        "<p>Historical best means the largest value in an unverified owner-reported list, not a confirmed leaderboard winner. "
        "The local HOLDOUT-DTI is not calibrated to organizer scores. Download availability is not permission to submit.</p>"
        '<div class="tablewrap" tabindex="0" role="region" aria-label="Nine-site decisions, scroll horizontally">'
        "<table><caption>All nine requested sites; fail-closed submission status</caption>"
        "<thead><tr><th>Site</th><th>Historical reference (unverified)</th>"
        "<th>Research-only download</th><th>Local evidence</th><th>Leaderboard estimate</th>"
        "<th>Uniqueness / submit?</th></tr></thead><tbody>"
        + "".join(rows)
        + '</tbody></table><p><a href="data/nine_site_download_decisions.json" download>'
        "Download machine-readable nine-site decisions</a></p></section>"
    )
