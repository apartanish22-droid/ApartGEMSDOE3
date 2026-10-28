#!/usr/bin/env python3
"""Fail-closed, data-independent check for current release authorization."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    card = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
    overlap = card["correlation_vs_registry"]["candidate_dots_within_3px_fraction"]
    limit = card["correlation_vs_registry"]["limit"]
    tif = ROOT / "docs/downloads/gemsdoe32-apart3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif"
    if overlap <= limit:
        raise SystemExit("This checker is specifically for the current known duplicate-stop release record.")
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise SystemExit("Unsafe release card: duplicate-stop is not marked negative / not-submittable")
    if card.get("slot_used") is not False or card.get("slot_authorized") is not False:
        raise SystemExit("Unsafe release card: slot must be unused and unauthorized")
    if not tif.is_file():
        raise SystemExit(f"Research artifact missing: {tif.relative_to(ROOT)}")
    actual_sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    if actual_sha != card["raster_sha256"]:
        raise SystemExit(f"Research artifact SHA-256 mismatch: {actual_sha}")
    page = (ROOT / "docs/release-status.html").read_text(encoding="utf-8")
    if "DO NOT SUBMIT THE CURRENT TIF" not in page or "NOT FOR SUBMISSION" not in page:
        raise SystemExit("Release page must clearly label the artifact as not for submission")
    print(
        "PASS: current card is negative, registry overlap exceeds the literal limit, "
        "slot is unused, research TIF hash matches, and the release page warns not to submit. "
        "This does not validate the GeoTIFF against competition data."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
