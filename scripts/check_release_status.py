#!/usr/bin/env python3
"""Fail closed on both the latest candidate and stale historical release records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(card: dict) -> None:
    """Validate a single card and reject promotion when the literal gate failed."""
    release = card.get("release_gate_decision", {})
    if card.get("verdict") != "negative" or release.get("verdict") != "negative":
        if card.get("correlation_vs_registry", {}).get("literal_all_rasters_final_passed") is not True:
            raise ValueError("literal all-registry uniqueness failure prevents promotion")
        raise ValueError("release card is not fail-closed")
    if card.get("correlation_vs_registry", {}).get("literal_all_rasters_final_passed") is not False:
        raise ValueError("literal all-registry uniqueness failure must remain explicit")


def _current_card(status: dict) -> tuple[dict, Path]:
    current = status.get("current_candidate") or {}
    source_paths = [part.strip() for part in str(current.get("source", "")).split(";")]
    card_path = next(
        (ROOT / source for source in source_paths
         if source.startswith("evidence/") and source.endswith("_run_card.json")
         and (ROOT / source).is_file()),
        None,
    )
    if card_path is None:
        raise SystemExit("Current status does not identify an existing evidence run card")
    return json.loads(card_path.read_text(encoding="utf-8")), card_path


def main():
    # The root run card is retained for historical compatibility, so validate it
    # as a separate fail-closed record rather than assuming it is current.
    historical = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
    if historical.get("ok_to_submit") is not False:
        raise SystemExit("Historical release must stay unauthorized")
    try:
        check(historical)
    except ValueError as exc:
        raise SystemExit(f"Historical card failed closed incorrectly: {exc}") from exc
    if historical.get("release_gate_decision", {}).get("gates", {}).get("final") is not False:
        raise SystemExit("Historical final-dot uniqueness failure must remain recorded")
    if historical.get("selector_required") is not True or historical.get("slot_used") is not False:
        raise SystemExit("Historical record must require separate selector and show no slot spent")
    old_tif = ROOT / historical["artifacts"]["primary_zeros_tif"]
    if hashlib.sha256(old_tif.read_bytes()).hexdigest() != historical["raster_sha256"]:
        raise SystemExit("Historical artifact checksum mismatch")

    status = json.loads((ROOT / "registry/current_status.json").read_text(encoding="utf-8"))
    current = status.get("current_candidate") or {}
    card, card_path = _current_card(status)
    if current.get("verdict") != "negative" or current.get("ok_to_submit") is not False:
        raise SystemExit("Current candidate must remain negative and not authorized")
    if current.get("slot_used") is not False or status.get("protocol_compliance", {}).get("overall", "").startswith("positive"):
        raise SystemExit("Current candidate has inconsistent slot or protocol status")
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise SystemExit(f"Current evidence card is not fail-closed: {card_path.relative_to(ROOT)}")
    artifact = current.get("artifact")
    if artifact != card.get("artifacts", {}).get("primary_zeros_tif"):
        raise SystemExit("Current status artifact does not match its evidence card")
    if current.get("sha256") != card.get("raster_sha256"):
        raise SystemExit("Current status SHA-256 does not match its evidence card")
    if current.get("candidate_id") != card.get("candidate_id"):
        raise SystemExit("Current status candidate id does not match its evidence card")
    duplicate = card.get("duplicate_gate_failure", {})
    if duplicate.get("final_dots_literal_gate_passed") is not False:
        raise SystemExit("Current literal registry failure must remain recorded")
    if card.get("scientific_integrity_gate", {}).get("passed") is not False:
        raise SystemExit("Current scientific-integrity failure must remain recorded")
    current_tif = ROOT / artifact
    if hashlib.sha256(current_tif.read_bytes()).hexdigest() != current["sha256"]:
        raise SystemExit("Current candidate artifact checksum mismatch")

    latest_data = json.loads((ROOT / "docs/data/latest-run-card.json").read_text(encoding="utf-8"))
    if latest_data.get("candidate_id") != current["candidate_id"] or latest_data.get("raster_sha256") != current["sha256"]:
        raise SystemExit("Machine-readable latest run card is stale")
    site_data = json.loads((ROOT / "docs/assets/site-data.json").read_text(encoding="utf-8"))
    if site_data.get("run_card", {}).get("candidate_id") != current["candidate_id"]:
        raise SystemExit("Machine-readable site data is stale")
    feed = json.loads((ROOT / "docs/data/feed.json").read_text(encoding="utf-8"))
    if feed.get("current_candidate", {}).get("run_card") != card_path.relative_to(ROOT).as_posix():
        raise SystemExit("Feed run-card pointer is stale")
    for name in ("index.html", "docs/index.html", "docs/executive-summary.html", "docs/release-status.html", "docs/submissions.html"):
        page = (ROOT / name).read_text(encoding="utf-8")
        if "DO NOT SUBMIT" not in page:
            raise SystemExit(f"Missing release warning: {name}")
        if current["candidate_id"] not in page or current["sha256"] not in page:
            raise SystemExit(f"Portal is stale relative to current candidate: {name}")
    for name in ("README.md",):
        page = (ROOT / name).read_text(encoding="utf-8")
        if "DO NOT SUBMIT" not in page or current["candidate_id"] not in page or current["sha256"] not in page:
            raise SystemExit(f"README is stale or missing release warning: {name}")
    print("PASS: current and historical candidates fail closed; hashes match; portal is current; no slot used")


if __name__ == "__main__":
    main()
