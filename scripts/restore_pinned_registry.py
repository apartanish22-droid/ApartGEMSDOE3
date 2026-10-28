#!/usr/bin/env python3
"""Restore and refresh the duplicate-gate registry via codeload.github.com tarball streaming.

Restores:
  1. All 9 focus repositories (`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`,
     `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`) into `.cache/registry/<repo>/<path>`
     and updates `registry/focus_registry_manifest.json` at live `main` (or pinned refs).
  2. All extra scored rasters (`registry/extra_scored_manifest.json`) into `.cache/extra/<repo>/<path>`.
  3. All sibling-org repositories listed in the prompt (`KANLERGEMSDOE1..3`, `WBGGEMSDOE1..3`,
     `GEMSDOEkarage1..3`, `ApartGEMSDOE1..2`, `EUGGEMSDOE1..3`, `GINNYGEMSDOE1..3`) into
     `.cache/sibling_orgs/`.

Uses `git ls-remote` + `https://codeload.github.com/<owner>/<repo>/tar.gz/<ref>` so it never hits
GitHub REST API rate limits.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
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
FOCUS_OWNER = "buffedlizard55-lab"
FOCUS_REPOS = [
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
SIBLING_REPOS = [
    ("kanlerxz87-cyber", "KANLERGEMSDOE1"),
    ("kanlerxz87-cyber", "KANLERGEMSDOE2"),
    ("kanlerxz87-cyber", "KANLERGEMSDOE3"),
    ("wingbangboozle1-lang", "WBGGEMSDOE1"),
    ("wingbangboozle1-lang", "WBGGEMSDOE2"),
    ("wingbangboozle1-lang", "WBGGEMSDOE3"),
    ("karagemop466-tech", "GEMSDOEkarage1"),
    ("karagemop466-tech", "GEMSDOEkarage2"),
    ("karagemop466-tech", "GEMSDOEkarage3"),
    ("apartanish22-droid", "ApartGEMSDOE1"),
    ("apartanish22-droid", "ApartGEMSDOE2"),
    ("eugboogieman123-ops", "EUGGEMSDOE1"),
    ("eugboogieman123-ops", "EUGGEMSDOE2"),
    ("eugboogieman123-ops", "EUGGEMSDOE3"),
    ("ginnymcfiner23-ux", "GINNYGEMSDOE1"),
    ("ginnymcfiner23-ux", "GINNYGEMSDOE2"),
    ("ginnymcfiner23-ux", "GINNYGEMSDOE3"),
    ("sassnarep3-star", "GEMSDOESASS1"),
    ("sassnarep3-star", "GEMSDOESASS2"),
    ("sassnarep3-star", "GEMSDOESASS3"),
    ("buffedlizard55-lab", "GEMSDOE91"),
    ("buffedlizard55-lab", "GEMSDOE92"),
]
PREFIXES = ("docs/", "inputs/", "archive/", "evidence/", "submission/", "submissions/", "outputs/")
MAX_BYTES = 8_000_000


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_head(owner: str, repo: str, branch: str = "main") -> str | None:
    try:
        out = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{owner}/{repo}.git", f"refs/heads/{branch}"],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        ).stdout.strip()
        if out:
            return out.split()[0]
    except Exception:
        return None
    return None


def extract_repo_tifs(owner: str, repo: str, ref: str, dest_root: Path, wanted_paths: set[str] | None = None) -> list[dict]:
    url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/{ref}"
    extracted = []
    with urllib.request.urlopen(url, timeout=120) as resp, tarfile.open(fileobj=resp, mode="r|gz") as tf:
        for member in tf:
            if not member.isfile() or "/" not in member.name:
                continue
            rel = member.name.split("/", 1)[1]
            if wanted_paths is not None:
                if rel not in wanted_paths:
                    continue
            else:
                if not rel.lower().endswith((".tif", ".tiff")):
                    continue
                if not rel.startswith(PREFIXES):
                    continue
                if member.size <= 0 or member.size > MAX_BYTES:
                    continue
            dest = dest_root / repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not (dest.exists() and dest.stat().st_size == member.size):
                src = tf.extractfile(member)
                if src is None:
                    continue
                tmp = dest.with_suffix(dest.suffix + ".partial")
                with tmp.open("wb") as out:
                    shutil.copyfileobj(src, out, 1 << 20)
                tmp.replace(dest)
            extracted.append(
                {
                    "owner": owner,
                    "repo": repo,
                    "ref": ref,
                    "path": rel,
                    "bytes": dest.stat().st_size,
                    "sha256": sha256_file(dest),
                    "local": str(dest.relative_to(ROOT)),
                    "status": "ok",
                }
            )
    return extracted


def restore_pinned_focus(manifest_path: Path, jobs: int = 6) -> dict:
    man = json.loads(manifest_path.read_text())
    by_repo_ref: dict[tuple[str, str], dict[str, dict]] = {}
    for r in man["rasters"]:
        if r.get("status") == "ok":
            by_repo_ref.setdefault((r["repo"], r["ref"]), {})[r["path"]] = r

    cache_root = ROOT / ".cache" / "registry"

    def _work(item: tuple[tuple[str, str], dict[str, dict]]) -> list[dict]:
        (repo, ref), path_map = item
        missing = set()
        results = []
        for path, entry in path_map.items():
            dest = ROOT / entry["local"]
            if dest.exists() and dest.stat().st_size == entry["bytes"] and sha256_file(dest) == entry["sha256"]:
                results.append({"local": entry["local"], "status": "present"})
            else:
                missing.add(path)
        if missing:
            got = extract_repo_tifs(FOCUS_OWNER, repo, ref, cache_root, wanted_paths=missing)
            got_by_path = {g["path"]: g for g in got}
            for path in missing:
                entry = path_map[path]
                g = got_by_path.get(path)
                if g is None:
                    results.append({"local": entry["local"], "status": "missing"})
                elif g["sha256"] != entry["sha256"]:
                    results.append({"local": entry["local"], "status": "mismatch", "got": g["sha256"]})
                else:
                    results.append({"local": entry["local"], "status": "restored"})
        return results

    all_res = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for batch in ex.map(_work, by_repo_ref.items()):
            all_res.extend(batch)
    counts: dict[str, int] = {}
    for r in all_res:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"total": len(all_res), "counts": counts}


def restore_extra_scored(manifest_path: Path, jobs: int = 6) -> dict:
    if not manifest_path.exists():
        return {"total": 0, "counts": {}}
    man = json.loads(manifest_path.read_text())
    by_repo_ref: dict[tuple[str, str], dict[str, dict]] = {}
    for r in man.get("rasters", []):
        if r.get("status") == "ok":
            by_repo_ref.setdefault((r["repo"], r["ref"]), {})[r["path"]] = r
    cache_root = ROOT / ".cache" / "extra"

    def _work(item: tuple[tuple[str, str], dict[str, dict]]) -> list[dict]:
        (repo, ref), path_map = item
        missing = set()
        results = []
        for path, entry in path_map.items():
            dest = ROOT / entry["local"]
            if dest.exists() and dest.stat().st_size == entry["bytes"] and sha256_file(dest) == entry["sha256"]:
                results.append({"local": entry["local"], "status": "present"})
            else:
                missing.add(path)
        if missing:
            got = extract_repo_tifs(FOCUS_OWNER, repo, ref, cache_root, wanted_paths=missing)
            got_by_path = {g["path"]: g for g in got}
            for path in missing:
                entry = path_map[path]
                g = got_by_path.get(path)
                if g and g["sha256"] == entry["sha256"]:
                    results.append({"local": entry["local"], "status": "restored"})
                else:
                    results.append({"local": entry["local"], "status": "failed"})
        return results

    all_res = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for batch in ex.map(_work, by_repo_ref.items()):
            all_res.extend(batch)
    counts: dict[str, int] = {}
    for r in all_res:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"total": len(all_res), "counts": counts}


def refresh_sibling_orgs(jobs: int = 6) -> dict:
    sib_root = ROOT / ".cache" / "sibling_orgs"
    sib_root.mkdir(parents=True, exist_ok=True)

    def _work(pair: tuple[str, str]) -> list[dict]:
        owner, repo = pair
        ref = resolve_head(owner, repo, "main")
        if not ref:
            return []
        try:
            return extract_repo_tifs(owner, repo, ref, sib_root / owner, wanted_paths=None)
        except Exception:
            return []

    rows = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for batch in ex.map(_work, SIBLING_REPOS):
            rows.extend(batch)
    rows.sort(key=lambda r: (r["owner"], r["repo"], r["path"]))
    (sib_root / "manifest.json").write_text(json.dumps(rows, indent=2) + "\n")
    return {"sibling_rasters": len(rows)}


def refresh_focus_live(manifest_path: Path, jobs: int = 6) -> dict:
    cache_root = ROOT / ".cache" / "registry"
    refs: dict[str, str] = {}

    def _work(repo: str) -> tuple[str, str, list[dict]]:
        ref = resolve_head(FOCUS_OWNER, repo, "main")
        if not ref:
            raise RuntimeError(f"Could not resolve HEAD for {repo}")
        got = extract_repo_tifs(FOCUS_OWNER, repo, ref, cache_root, wanted_paths=None)
        for g in got:
            g.pop("owner", None)
        return repo, ref, got

    all_rows = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for repo, ref, got in ex.map(_work, FOCUS_REPOS):
            refs[repo] = ref
            all_rows.extend(got)
    all_rows.sort(key=lambda r: (r["repo"], r["path"]))
    manifest = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "owner": FOCUS_OWNER,
        "refs": refs,
        "prefixes": ["docs/", "inputs/", "archive/", "evidence/"],
        "max_bytes": MAX_BYTES,
        "n_rasters": len(all_rows),
        "n_failed": 0,
        "rasters": all_rows,
        "note": "Registry for the duplicate gate. Hashes are of the fetched bytes at the pinned refs.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
    return {"focus_rasters": len(all_rows), "refs": refs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--refresh-live", action="store_true", help="Refresh focus_registry_manifest.json from live main")
    args = ap.parse_args()

    fman = ROOT / "registry" / "focus_registry_manifest.json"
    eman = ROOT / "registry" / "extra_scored_manifest.json"

    if args.refresh_live:
        f_res = refresh_focus_live(fman, jobs=args.jobs)
    else:
        f_res = restore_pinned_focus(fman, jobs=args.jobs)
    e_res = restore_extra_scored(eman, jobs=args.jobs)
    s_res = refresh_sibling_orgs(jobs=args.jobs)
    out = {"focus": f_res, "extra_scored": e_res, "sibling_orgs": s_res}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
