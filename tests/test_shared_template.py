import json
import sys
from pathlib import Path

import numpy as np
import pytest

from audit_priority import ROOT, git_blob_file
from cache_shared_template import cache_template
from shared_import import load_shared_module


def shared_root():
    manifest = json.loads((ROOT / "registry/shared_template.json").read_text())
    root = ROOT / ".cache/shared_template" / manifest["ref"]
    if not root.exists():
        pytest.skip("Shared source cache absent; run scripts/cache_shared_template.py to exercise integration")
    return root


def test_shared_sources_are_byte_exact():
    root = shared_root()
    manifest = json.loads((ROOT / "registry/shared_template.json").read_text())
    for entry in manifest["files"]:
        file = root / entry["path"]
        assert file.stat().st_size == entry["size"]
        assert git_blob_file(file) == entry["git_blob"]
    assert cache_template(offline=True) == root


def test_shared_import_does_not_use_an_already_imported_gems(monkeypatch):
    import types
    root = shared_root()
    foreign = types.ModuleType("gems")
    monkeypatch.setitem(sys.modules, "gems", foreign)
    module = load_shared_module(root, "submission")
    assert Path(module.__file__).resolve() == (root / "src/gems/submission.py").resolve()
    assert sys.modules["gems"] is foreign


def test_shared_import_rejects_modified_cached_source(tmp_path):
    import shutil
    root = shared_root()
    copied = tmp_path / root.name
    shutil.copytree(root, copied)
    with (copied / 'src/gems/submission.py').open('a') as handle:
        handle.write('\n# tampered\n')
    with pytest.raises(ValueError, match='missing or modified'):
        load_shared_module(copied, 'submission')


def test_shared_fast_metric_agrees_with_exact_and_masks_known_pixels():
    root = shared_root()
    metric = load_shared_module(root, "metric")
    dti_components_exact, dti_score_fast = metric.dti_components_exact, metric.dti_score_fast
    pred = np.zeros((9, 9), np.float32)
    truth = np.zeros_like(pred)
    known = np.zeros_like(pred, bool)
    pred[4, 3] = pred[0, 0] = 1
    truth[4, 4] = 1
    known[0, 0] = True
    exact = dti_components_exact(pred, truth, catalogue_mask=known)
    fast = dti_score_fast(pred, truth, catalogue_mask=known)
    for key in ("TP_w", "FP_w", "FN_w", "dti"):
        assert fast[key] == pytest.approx(exact[key])
    assert exact["TP_w"] == pytest.approx(2 / 3)
    assert exact["FP_w"] == pytest.approx(1 / 3)
    assert fast["n_emitted"] == 1  # the known pixel was excluded exactly
    pred[3, 3] = np.nan
    with pytest.raises(ValueError):
        dti_score_fast(pred, truth, catalogue_mask=known)


def test_shared_canary_flags_a_known_label_feature():
    root = shared_root()
    SegmentHoldout = load_shared_module(root, "holdout").SegmentHoldout
    fp = np.ones((60, 60), bool)
    labels = np.zeros_like(fp)
    for y, x in [(12, 12), (12, 45), (45, 12), (45, 45)]:
        labels[y:y + 3, x] = True
    context = SegmentHoldout(fp, labels, buffer_px=3)
    diagnostic = context.canary({"leaked_labels": labels.astype(np.float32)}, max_per_class=300)
    assert diagnostic["features"]["leaked_labels"]["leakage_suspected"] is True
    assert diagnostic["passed"] is False
