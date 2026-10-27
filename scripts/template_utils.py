"""Hash and validate the user-requested, locally restored shared template."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "vendor/template-provenance.json"
DEFAULT_DEST = ROOT / "vendor/gems57"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def verify_bytes(data: bytes, item: dict) -> bool:
    return (hashlib.sha256(data).hexdigest() == item["sha256"]
            and git_blob(data) == item["git_blob"])


def template_records() -> tuple[dict, list[dict]]:
    provenance = json.loads(PROVENANCE.read_text())
    files = provenance["files"]
    names = [Path(x["local"]).name for x in files]
    if len(names) != len(set(names)) or any(
        x["local"] != f"vendor/gems57/{name}" or not name.endswith(".py")
        for x, name in zip(files, names)
    ):
        raise ValueError("invalid template provenance file paths")
    return provenance, files


def verify_template(destination: Path = DEFAULT_DEST) -> None:
    """Fail before import if a template file is missing, changed or unindexed."""
    _, files = template_records()
    expected = {Path(item["local"]).name for item in files}
    actual = {p.name for p in destination.glob("*.py")} if destination.is_dir() else set()
    if actual != expected:
        raise ValueError("shared template missing or contains unindexed Python files; run python scripts/fetch_template.py")
    for item in files:
        path = destination / Path(item["local"]).name
        if not verify_bytes(path.read_bytes(), item):
            raise ValueError(f"shared template hash mismatch: {path}; run python scripts/fetch_template.py")
