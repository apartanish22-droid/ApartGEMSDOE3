#!/usr/bin/env python3
"""Index pinned peer TIFF paths and check source freshness; never download/submit them.

The index is a list of Git objects, NOT an exhaustive global registry and NOT a
novelty result. Commits are deliberately pinned; moved heads require a new audit.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from io_safety import validate_output_path

ROOT = Path(__file__).resolve().parents[1]


def github_json(endpoint: str) -> dict:
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, check=True, timeout=60)
    return json.loads(result.stdout)


def get_tree(row: dict) -> dict:
    tree = github_json(f"repos/{row['repo']}/git/trees/{row['ref']}?recursive=1")
    if tree.get("truncated") or not isinstance(tree.get("tree"), list):
        raise RuntimeError(f"Incomplete Git tree for {row['repo']} at {row['ref']}")
    indexed = [
        {"path": item["path"], "git_blob": item["sha"], "size": item["size"]}
        for item in tree["tree"]
        if item.get("type") == "blob" and item["path"].lower().endswith((".tif", ".tiff"))
    ]
    selected = next((item for item in indexed if item["path"] == row["path"]), None)
    if not selected or selected["git_blob"] != row["git_blob"] or selected["size"] != row["size"]:
        raise RuntimeError(f"Pinned historical file differs from its pinned tree: {row['site']}")
    return {"site": row["site"], "repo": row["repo"], "ref": row["ref"], "files": indexed}


def get_head(row: dict) -> dict:
    try:
        head = github_json(f"repos/{row['repo']}/commits/main")
        sha = head["sha"]
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Invalid GitHub commit SHA")
        return {"site": row["site"], "pinned": row["ref"], "head": sha, "state": "unchanged" if sha == row["ref"] else "changed; re-audit required"}
    except (subprocess.SubprocessError, KeyError, ValueError, OSError) as exc:
        return {"site": row["site"], "pinned": row["ref"], "head": None, "state": "unknown; do not assume fresh", "error": str(exc)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--heads", action="store_true", help="Check HEAD freshness instead of rebuilding the pinned inventory")
    p.add_argument("--output", type=Path, help="Destination JSON (default depends on mode)")
    args = p.parse_args()
    manifest = ROOT / "registry/focus_sites.json"
    out = args.output or (ROOT / "evidence/source_freshness.json" if args.heads else ROOT / "registry/tiff_inventory.json")
    validate_output_path(out, (manifest,))
    rows = json.loads(manifest.read_text())["sites"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(get_head if args.heads else get_tree, rows))
    data = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Nine historical repository heads only; excludes the lattice and wider registry, and does not check leaderboard, score or slot status" if args.heads else "All TIFF paths in pinned nine repository trees, including non-submissions and data layers. Indexed only; not downloaded, filtered, or compared. Excludes other sites and later commits.",
        "sources": results,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {out}; sources={len(results)}" + (f"; TIFF paths={sum(len(r['files']) for r in results)}" if not args.heads else ""))
    if args.heads and any(r["state"] != "unchanged" for r in results):
        raise SystemExit("One or more historical heads changed or could not be checked; re-audit required")


if __name__ == "__main__":
    main()
