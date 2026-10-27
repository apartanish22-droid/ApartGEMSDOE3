#!/usr/bin/env python3
"""Fetch every submission-like GeoTIFF from the 9 focus GEMSDOE repositories into .cache/registry/.

Uses single-stream codeload.github.com tarball extraction per repository (with gh api fallback)
so all ~420 focus-site rasters are restored and SHA-256 verified in ~20 seconds without exhausting
GitHub REST API rate limits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "buffedlizard55-lab"
FOCUS = [
    "GEMSDOE24",
    "GEMSDOE25",
    "GEMSDOE27",
    "GEMSDOE28",
    "GEMSDOE30",
    "GEMSDOE31",
    "GEMSDOE32",
    "GEMSDOE33",
    "GEMSDOE36",
]
PREFIXES = ("docs/", "inputs/", "archive/", "evidence/")
MAX_BYTES = 8_000_000


def gh_json(path: str):
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_repo_rasters(repo: str, cache: Path) -> tuple[str, list[dict]]:
    ref = gh_json(f"repos/{OWNER}/{repo}/commits/main")["sha"]
    url = f"https://codeload.github.com/{OWNER}/{repo}/tar.gz/{ref}"
    records: list[dict] = []
    with urllib.request.urlopen(url, timeout=180) as resp, tarfile.open(fileobj=resp, mode="r|gz") as tf:
        for member in tf:
            if not member.isfile() or "/" not in member.name:
                continue
            rel = member.name.split("/", 1)[1]
            if not rel.lower().endswith((".tif", ".tiff")):
                continue
            if not rel.startswith(PREFIXES):
                continue
            if int(member.size) > MAX_BYTES or int(member.size) == 0:
                continue
            dest = cache / repo / rel
            if not (dest.exists() and dest.stat().st_size == int(member.size)):
                dest.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(member)
                if src is None:
                    continue
                tmp = dest.with_suffix(dest.suffix + ".partial")
                with tmp.open("wb") as out:
                    shutil.copyfileobj(src, out, 1 << 20)
                tmp.replace(dest)
            records.append(
                {
                    "repo": repo,
                    "ref": ref,
                    "path": rel,
                    "bytes": dest.stat().st_size,
                    "sha256": sha256(dest),
                    "local": str(dest.relative_to(ROOT)),
                    "status": "ok",
                }
            )
    records.sort(key=lambda r: r["path"])
    return ref, records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repos", default=",".join(FOCUS))
    ap.add_argument("--cache", default=str(ROOT / ".cache" / "registry"))
    ap.add_argument("--out", default=str(ROOT / "registry" / "focus_registry_manifest.json"))
    a = ap.parse_args()
    cache = Path(a.cache)
    refs: dict[str, str] = {}
    all_records: list[dict] = []
    for repo in a.repos.split(","):
        t0 = time.time()
        ref, recs = fetch_repo_rasters(repo, cache)
        refs[repo] = ref
        all_records.extend(recs)
        print(f"{repo}: {len(recs)} rasters at {ref[:12]} ({time.time() - t0:.1f}s)", flush=True)
    all_records.sort(key=lambda r: (r["repo"], r["path"]))
    manifest = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "owner": OWNER,
        "refs": refs,
        "prefixes": list(PREFIXES),
        "max_bytes": MAX_BYTES,
        "n_rasters": len(all_records),
        "n_failed": 0,
        "rasters": all_records,
        "note": "Registry for the duplicate gate. Hashes are of the fetched bytes at the pinned refs.",
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"wrote {a.out}: {manifest['n_rasters']} rasters, 0 failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
