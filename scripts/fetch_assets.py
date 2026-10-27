#!/usr/bin/env python3
"""Restore hash-pinned third-party mirrors into an ignored cache, never into Git.

The content pins establish byte identity only. They are not an organizer data
receipt, or proof that competition terms authorize use of a third-party mirror.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry/input_manifest.json"
DEFAULT_CACHE = ROOT / ".cache/inputs"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(record: dict, cache: Path) -> dict:
    dest = (cache / record["destination"]).resolve()
    if cache.resolve() not in dest.parents:
        raise ValueError("unsafe destination in manifest")
    if dest.exists() and sha256_file(dest) == record["sha256"]:
        return {"id": record["id"], "status": "verified cached", "sha256": record["sha256"]}
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(dest.suffix + ".partial")
    endpoint = f"repos/{record['repo']}/contents/{record['path']}?ref={record['ref']}"
    try:
        with temporary.open("wb") as stream:
            completed = subprocess.run(
                ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw+json"],
                stdout=stream, stderr=subprocess.PIPE, timeout=300, check=False,
            )
        if completed.returncode:
            raise RuntimeError(f"GitHub fetch failed for {record['id']}: {completed.stderr.decode(errors='replace')[:300]}")
        if record.get("bytes") is not None and temporary.stat().st_size != record["bytes"]:
            raise ValueError(f"unexpected byte count for {record['id']}")
        got = sha256_file(temporary)
        if got != record["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {record['id']}: {got}")
        os.replace(temporary, dest)
    finally:
        temporary.unlink(missing_ok=True)
    return {"id": record["id"], "status": "restored", "sha256": record["sha256"]}


def assemble(manifest: dict, cache: Path) -> dict:
    spec = manifest["assembled_feature"]
    target = cache / spec["destination"]
    if target.exists() and sha256_file(target) == spec["sha256"]:
        return {"id": "training_features", "status": "verified cached", "sha256": spec["sha256"]}
    lookup = {x["id"]: x for x in manifest["files"]}
    tmp = target.with_suffix(".assembling")
    try:
        with tmp.open("wb") as out:
            for ident in spec["parts"]:
                record = lookup[ident]
                part = cache / record["destination"]
                if not part.is_file() or sha256_file(part) != record["sha256"]:
                    raise ValueError(f"missing or changed feature part: {ident}")
                with part.open("rb") as stream:
                    shutil.copyfileobj(stream, out, 1024 * 1024)
        if tmp.stat().st_size != spec["bytes"] or sha256_file(tmp) != spec["sha256"]:
            raise ValueError("assembled feature TIFF did not match its pin")
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)
    return {"id": "training_features", "status": "assembled", "sha256": spec["sha256"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--groups", nargs="+", choices=["core", "history", "features", "external"],
                    default=["core", "history"])
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args(argv)
    if args.workers < 1 or args.workers > 4:
        ap.error("--workers must be between 1 and 4")
    if not shutil.which("gh"):
        ap.error("the GitHub CLI (gh) is required for the public mirror")
    manifest = json.loads(MANIFEST.read_text())
    records = [item for item in manifest["files"] if item["group"] in args.groups]
    args.cache.mkdir(parents=True, exist_ok=True)
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda item: fetch(item, args.cache), records))
        if "features" in args.groups:
            results.append(assemble(manifest, args.cache))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Asset restoration FAILED (no promotion): {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"provenance": manifest["provenance"], "files": results}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
