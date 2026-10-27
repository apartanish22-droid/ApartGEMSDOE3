"""Load the pinned shared package under a private import namespace, byte-verified.

The namespace avoids silently importing a different local ``gems`` package when
both this repository and the upstream template are present in one process. It
does not modify or fork the upstream source.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

from audit_priority import ROOT, git_blob_file


def load_shared_module(root: Path, module: str):
    manifest = json.loads((ROOT / "registry/shared_template.json").read_text())
    root = Path(root).resolve()
    if (root.name != manifest["ref"] or not module.isidentifier()
            or f"src/gems/{module}.py" not in {entry["path"] for entry in manifest["files"]}):
        raise ValueError("Invalid shared-template root or module name")
    for entry in manifest["files"]:
        target = root / entry["path"]
        if not target.is_file() or target.stat().st_size != entry["size"] or git_blob_file(target) != entry["git_blob"]:
            raise ValueError(f"Shared-template source is missing or modified: {entry['path']}")
    package_name = "_apartgems_shared_" + manifest["ref"]
    package_dir = root / "src/gems"
    existing = sys.modules.get(package_name)
    if existing is None:
        spec = importlib.util.spec_from_file_location(
            package_name, package_dir / "__init__.py", submodule_search_locations=[str(package_dir)]
        )
        if spec is None or spec.loader is None:
            raise ImportError("Unable to load pinned shared template")
        package = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = package
        try:
            spec.loader.exec_module(package)
        except BaseException:
            sys.modules.pop(package_name, None)
            raise
    elif Path(existing.__file__).resolve() != (package_dir / "__init__.py").resolve():
        raise ImportError("Conflicting shared-template import namespace")
    return importlib.import_module(f"{package_name}.{module}")
