#!/usr/bin/env python3
"""Data-independent regression check that current release authorization fails closed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    card = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
    tif = ROOT / card["artifacts"]["primary_zeros_tif"]
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise SystemExit("Unsafe release card: candidate must be negative and not submittable")
    if card.get("selector_required") is not True:
        raise SystemExit("Unsafe release card: separate selector must be required")
    if card.get("release_gate_decision", {}).get("slot_used") is not False:
        raise SystemExit("Unsafe release card: no slot may be recorded as used")
    if card.get("correlation_and_overlap_vs_registry", {}).get("literal_all_rasters_final_passed") is not False:
        raise SystemExit("Unsafe release card: literal all-registry uniqueness failure must remain explicit")
    if card.get("scientific_integrity_gate", {}).get("passed") is not False:
        raise SystemExit("Unsafe release card: scientific-integrity issue must remain open")
    if not tif.is_file():
        raise SystemExit(f"Research artifact missing: {tif.relative_to(ROOT)}")
    actual_sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    if actual_sha != card["raster_sha256"]:
        raise SystemExit(f"Research artifact SHA-256 mismatch: {actual_sha}")
    page = (ROOT / "docs/release-status.html").read_text(encoding="utf-8")
    if "NO FILE AUTHORIZED" not in page or "DO NOT SUBMIT" not in page:
        raise SystemExit("Release page must clearly label the artifact as not for submission")
    print("PASS: negative run card, selector required, literal uniqueness fails, scientific issue open, TIF hash matches, release page says DO NOT SUBMIT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
