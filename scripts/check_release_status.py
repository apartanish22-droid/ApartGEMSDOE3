#!/usr/bin/env python3
"""Data-independent regression check for current run_card.json & release portal integrity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    card = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
    tif_rel = card.get("artifacts", {}).get("primary_zeros_tif") or card["download_files"]["primary_download_path"]
    tif = ROOT / tif_rel
    if card.get("verdict") != "promote":
        raise SystemExit(f"Unexpected run_card verdict: {card.get('verdict')}")
    if card.get("selector_required") is not True:
        raise SystemExit("Unsafe release card: separate selector must be required")
    if card.get("slot_used") is not False or card.get("release_gate_decision", {}).get("slot_used") is not False:
        raise SystemExit("Unsafe release card: no slot may be recorded as used")
    if not all(card.get("validator", {}).values()):
        raise SystemExit("Validator flags must all be True")
    if not all(card.get("release_gate_decision", {}).get("gates", {}).values()):
        raise SystemExit("All 7 release_gate_decision gates must be True")
    if card.get("correlation_vs_registry", {}).get("literal_all_rasters_final_passed") is not False:
        raise SystemExit("IR-51-LATTICE-01 literal lattice probe status must remain explicitly documented")
    if not tif.is_file():
        raise SystemExit(f"Promoted artifact missing: {tif.relative_to(ROOT)}")
    actual_sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    if actual_sha != card["raster_sha256"]:
        raise SystemExit(f"Artifact SHA-256 mismatch: {actual_sha}")
    page = (ROOT / "docs/release-status.html").read_text(encoding="utf-8")
    if card["raster_sha256"][:16] not in page or "DO NOT SUBMIT" not in page:
        raise SystemExit("Release status page must document primary SHA-256 and DO NOT SUBMIT on superseded files")
    print("PASS: H-APART3-2 (CSHD) run card verified, selector_required=True, slot_used=False, SHA-256 matches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
