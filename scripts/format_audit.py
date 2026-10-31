"""Format-audit every downloadable GeoTIFF in docs/downloads against the template.

Writes evidence/format_audit_<date>.json with SHA-256, pass/fail, and the failing
check for each file. This explains the portal error "Predicted values must be in
range [0, 1]": -nan variants carry NaN outside the footprint and fail the
whole-array check, while -zeros variants pass.

This is a FORMAT check only. It is not scientific, uniqueness, or weekly-slot
authorization (see registry/current_status.json for the gate rules).

Usage:
    python scripts/format_audit.py --template .cache/gems_data/sample_submission.tif
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe32.submission import validate_submission_geotiff  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--downloads", type=Path, default=ROOT / "docs" / "downloads")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    out = (args.out or ROOT / "evidence" / f"format_audit_{stamp}.json").resolve()

    rows = []
    for tif in sorted(args.downloads.glob("*.tif")):
        report = validate_submission_geotiff(tif, args.template, strict_whole_array_finite=True)
        d = report.to_dict()
        failed = [c["name"] for c in d["checks"] if not c["passed"]]
        rows.append(
            {
                "file": tif.relative_to(ROOT).as_posix(),
                "sha256": sha256(tif),
                "bytes": tif.stat().st_size,
                "portal_format_pass": bool(d["passed"]),
                "failed_checks": failed,
                "variant": "zeros" if "-zeros" in tif.name else ("nan" if "-nan" in tif.name else "other"),
            }
        )

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "template": args.template.as_posix(),
        "template_note": "Owner-mirror template restored by SHA-256 (not organizer-authenticated).",
        "scope": "FORMAT ONLY. Not scientific, uniqueness, or weekly-slot authorization.",
        "files_total": len(rows),
        "files_pass": sum(r["portal_format_pass"] for r in rows),
        "files_fail": sum(not r["portal_format_pass"] for r in rows),
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {summary['files_pass']} pass / {summary['files_fail']} fail of {summary['files_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
