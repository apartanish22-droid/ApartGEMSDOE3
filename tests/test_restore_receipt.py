"""Regression test: a partial restore must not erase receipt entries from earlier runs."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_restore_module():
    spec = importlib.util.spec_from_file_location("restore_data", ROOT / "scripts" / "restore_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_merge_receipt_keeps_entries_from_other_groups(tmp_path: Path) -> None:
    mod = _load_restore_module()
    receipt = tmp_path / "restore_receipt.json"
    core = [{"id": "labels", "group": "core", "status": "restored", "sha256": "aa", "bytes": 1, "dest": "labels.tif"}]
    scored = [{"id": "scored_x", "group": "scored", "status": "present", "sha256": "bb", "bytes": 2, "dest": "scored/x.tif"}]

    first = mod.merge_receipt(receipt, core, "x")
    receipt.write_text(json.dumps(first))
    second = mod.merge_receipt(receipt, scored, "x")

    ids = [f["id"] for f in second["files"]]
    assert ids == ["labels", "scored_x"]
    assert second["verified_files_count"] == 2


def test_merge_receipt_replaces_same_id(tmp_path: Path) -> None:
    mod = _load_restore_module()
    receipt = tmp_path / "restore_receipt.json"
    old = [{"id": "labels", "group": "core", "status": "restored", "sha256": "aa", "bytes": 1, "dest": "labels.tif"}]
    new = [{"id": "labels", "group": "core", "status": "present", "sha256": "aa", "bytes": 1, "dest": "labels.tif"}]
    receipt.write_text(json.dumps(mod.merge_receipt(receipt, old, "x")))
    merged = mod.merge_receipt(receipt, new, "x")
    assert len(merged["files"]) == 1
    assert merged["files"][0]["status"] == "present"


def test_merge_receipt_tolerates_corrupt_receipt(tmp_path: Path) -> None:
    mod = _load_restore_module()
    receipt = tmp_path / "restore_receipt.json"
    receipt.write_text("{not json")
    merged = mod.merge_receipt(receipt, [{"id": "a", "status": "present"}], "x")
    assert [f["id"] for f in merged["files"]] == ["a"]
