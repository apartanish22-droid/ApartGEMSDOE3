from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from scipy import ndimage

from gems57 import evaluate_holdout, holdout, metric


def test_shared_evaluator_pools_exact_terms_and_pixel_masks():
    shape = (16, 16)
    truth = np.zeros(shape, bool); truth[3, 3] = truth[9, 9] = truth[2, 8] = True
    visible = np.zeros(shape, bool); visible[2, 8] = True
    masked_known = visible.copy(); masked_known[5, 5] = True
    pred = np.zeros(shape, np.float32)
    pred[3, 4] = .6; pred[9, 9] = 1; pred[2, 8] = 1; pred[5, 5] = 1; pred[15, 15] = .5
    region = np.ones(shape, bool); valid = np.ones(shape, bool)
    fold = {"truth": truth, "visible": visible, "masked_known": masked_known, "region": region}
    result, terms = evaluate_holdout.evaluate(pred, fold, valid, block_side=4)
    direct = metric.dti_exact(pred, truth, valid=valid, known=masked_known)
    assert result["evidence_class"] == "HOLDOUT-DTI"
    assert result["evaluator_version"] == evaluate_holdout.VERSION
    assert result["n_truth"] == 2 and result["n_emitted"] == 3
    np.testing.assert_allclose(terms.sum(axis=0), [direct["tp"], direct["fp"], direct["fn"], 2])
    assert result["dti"] == pytest.approx(direct["dti"])
    # A block with no truth can still contribute false positives to pooled terms.
    assert any(t[3] == 0 and t[1] > 0 for t in terms)
    summary = evaluate_holdout.pooled_summary({"candidate": terms, "control": terms.copy()}, draws=100, seed=7, candidate="candidate")
    arm = summary["scores"]["candidate"]
    assert arm["withheld_positive_pixels"] == 2 and len(arm["ci95"]) == 2
    assert summary["paired_differences"]["control"]["ci95"] == [0, 0]
    assert "not a leaderboard interval" in summary["bootstrap"]["caveat"]
    wrong = terms.copy(); wrong[0, 3] += 1
    with pytest.raises(ValueError, match="same integer truth count"):
        evaluate_holdout.pooled_summary({"candidate": terms, "control": wrong}, draws=100, candidate="candidate")


def test_buffered_component_draw_hides_whole_features_from_visible_catalogue():
    shape = (80, 80)
    footprint = np.ones(shape, bool)
    catalogue = np.zeros(shape, bool)
    # Sixteen deliberately separated synthetic line components over four quadrants.
    for y in (10, 20, 50, 60):
        for x in (10, 20, 50, 60):
            catalogue[y, x:x + 3] = True
    grid = SimpleNamespace(footprint=footprint, catalogue=catalogue)
    folds, quadrant = holdout.buffered_component_draw(grid, seed=29, hide_frac=.4, buffer_px=3, boundary_px=4)
    assert len(folds) == 4 and quadrant.shape == shape
    hidden = folds[0]["hidden_all"]
    assert hidden.any() and all(np.array_equal(f["hidden_all"], hidden) for f in folds)
    components, n = ndimage.label(catalogue, np.ones((3, 3), bool))
    for cid in range(1, n + 1):
        support = components == cid
        assert not hidden[support].any() or hidden[support].all()
    visible = folds[0]["visible"]
    assert not (visible & hidden).any()
    assert ndimage.distance_transform_edt(~visible)[hidden].min() > 3
    # Suppressed catalogue points in the feature buffer remain masked in scoring.
    assert np.array_equal(folds[0]["masked_known"], catalogue & ~hidden)
    for fold in folds:
        assert not (fold["truth"] & ~fold["region"]).any()
        assert fold["receipt"]["evaluation_region_label_blind"]


def test_shared_evaluator_rejects_invalid_and_empty_fold():
    truth = np.zeros((5, 5), bool)
    fold = {"truth": truth, "visible": truth, "region": np.ones_like(truth)}
    with pytest.raises(ValueError, match="must contain positives"):
        evaluate_holdout.evaluate(np.zeros((5, 5)), fold, np.ones_like(truth))
    invalid = np.zeros((5, 5)); invalid[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        evaluate_holdout.evaluate(invalid, fold, np.ones_like(truth))
