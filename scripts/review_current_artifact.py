#!/usr/bin/env python3
"""Recheck the saved research artifact and refresh the fail-closed release card."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems.current_review import review_current_best  # noqa: E402
from gems.executive_decisions import build_decisions  # noqa: E402


def main() -> int:
    result = review_current_best(ROOT)
    output = ROOT / "docs/data/latest-run-card.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    decisions = build_decisions(ROOT, result)
    decisions_output = ROOT / "docs/data/nine_site_download_decisions.json"
    decisions_output.write_text(json.dumps(decisions, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": result["submission_name"],
        "sha256": result["raster_sha256"],
        "HOLDOUT-DTI": result["holdout_dti"],
        "focus_rasters_pairwise_pass": result["novel_vs_each_focus_raster_under_thresholds"],
        "independent_lattice_audit": result["independent_lattice_audit"],
        "format_valid": result["validator_output"]["format_valid"],
        "official_format_compliant": result["validator_output"]["official_format_compliant"],
        "selector_decision": result["selector"]["decision"],
        "verdict": result["verdict"],
        "status_file": str(output.relative_to(ROOT)),
        "nine_site_decisions": str(decisions_output.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
