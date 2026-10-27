from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess

import pytest

import fetch_template
from template_utils import DEFAULT_DEST, git_blob, template_records, verify_template


def test_restore_uses_cached_bytes_only_after_hash_check(tmp_path, monkeypatch):
    _, records = template_records()
    record = records[0]
    source = DEFAULT_DEST / Path(record["local"]).name
    payload = source.read_bytes()
    target = tmp_path / source.name
    target.write_bytes(payload)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("verified cached bytes should not trigger download"))
    assert fetch_template.restore(record, repo="owner/repo", commit="a" * 40, destination=tmp_path).startswith("verified")
    assert hashlib.sha256(payload).hexdigest() == record["sha256"]
    assert git_blob(payload) == record["git_blob"]


def test_restore_rejects_tampered_download_without_replacing_existing_file(tmp_path, monkeypatch):
    _, records = template_records()
    record = records[0]
    target = tmp_path / Path(record["local"]).name
    target.write_bytes(b"old corrupt cache")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: SimpleProcess(b"tampered download", 0))
    with pytest.raises(ValueError, match="hash mismatch"):
        fetch_template.restore(record, repo="owner/repo", commit="a" * 40, destination=tmp_path)
    assert target.read_bytes() == b"old corrupt cache"
    assert list(tmp_path.iterdir()) == [target]


class SimpleProcess:
    def __init__(self, stdout, returncode):
        self.stdout, self.returncode, self.stderr = stdout, returncode, b"failed"


def test_template_verification_fails_on_missing_tampering_and_unindexed_code(tmp_path):
    shutil.copytree(DEFAULT_DEST, tmp_path / "template", ignore=shutil.ignore_patterns("__pycache__"))
    dest = tmp_path / "template"
    verify_template(dest)
    metric = dest / "metric.py"
    content = metric.read_bytes()
    metric.write_bytes(content + b"\n# changed\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_template(dest)
    metric.write_bytes(content)
    (dest / "unexpected.py").write_text("# no unindexed imports\n")
    with pytest.raises(ValueError, match="unindexed"):
        verify_template(dest)
    (dest / "unexpected.py").unlink()
    metric.unlink()
    with pytest.raises(ValueError, match="missing"):
        verify_template(dest)
