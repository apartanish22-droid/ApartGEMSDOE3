#!/usr/bin/env python3
"""Restore the pinned shared template locally, without redistributing its bytes.

The upstream repository had no license metadata at the time of review. Restored
files are ignored by Git and checked against both Git blob and SHA-256 pins.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from template_utils import DEFAULT_DEST, template_records, verify_bytes, verify_template


def restore(item: dict, *, repo: str, commit: str, destination: Path) -> str:
    target = destination / Path(item["local"]).name
    if target.is_file() and verify_bytes(target.read_bytes(), item):
        return f"verified {target.name}"
    endpoint = f"repos/{repo}/contents/{item['upstream_path']}?ref={commit}"
    completed = subprocess.run(
        ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw+json"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"template fetch failed for {target.name}: {completed.stderr.decode(errors='replace')[:200]}")
    if not verify_bytes(completed.stdout, item):
        raise ValueError(f"template hash mismatch for {target.name}")
    destination.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=destination)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(completed.stdout)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return f"restored {target.name}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 4:
        parser.error("--workers must be between 1 and 4")
    if not shutil.which("gh"):
        parser.error("GitHub CLI (gh) is required")
    try:
        provenance, files = template_records()
        repo = provenance["upstream"].removeprefix("https://github.com/").rstrip("/")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda item: restore(item, repo=repo, commit=provenance["commit"], destination=args.destination), files))
        verify_template(args.destination)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"TEMPLATE RESTORE FAILED (no promotion): {exc}", file=sys.stderr)
        return 1
    print(f"Verified {len(results)} pinned shared template files in {args.destination}; no source changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
