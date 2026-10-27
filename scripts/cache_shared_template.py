#!/usr/bin/env python3
"""Cache the upstream GEMSDOE24 evaluator/writer byte-for-byte; no private fork.

This only provides pinned source files, not the missing feature stack, complete
upstream package, assigned lane, comparison registry, or slot authorization.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from audit_priority import ROOT, git_blob_file, verified_cached_file


def cache_template(offline: bool = False) -> Path:
    manifest = json.loads((ROOT / "registry/shared_template.json").read_text())
    destination = ROOT / ".cache/shared_template" / manifest["ref"]
    for item in manifest["files"]:
        source = verified_cached_file(item, ROOT / ".cache/shared_blobs", offline=offline)
        target = destination / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or git_blob_file(target) != item["git_blob"]:
            temporary = target.with_suffix(target.suffix + ".tmp")
            shutil.copyfile(source, temporary)
            if git_blob_file(temporary) != item["git_blob"]:
                temporary.unlink(missing_ok=True)
                raise ValueError(f"Shared-template blob mismatch: {item['path']}")
            temporary.replace(target)
    return destination


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--offline", action="store_true")
    args = p.parse_args()
    print(json.dumps({"cache": str(cache_template(args.offline)), "byte_exact": True, "experiment_ready": False, "submission_authorized": False}, indent=2))


if __name__ == "__main__":
    main()
