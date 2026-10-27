from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import spearmanr

from audit_prior import binary_rank_correlation, lower_overlap_bound
from gems57 import metric, uniqueness


def test_binary_rank_correlation_matches_scipy_ties():
    rng = np.random.default_rng(901)
    for _ in range(20):
        a = rng.random((7, 11)) < .3
        b = rng.random((7, 11)) < .15
        footprint = rng.random((7, 11)) < .8
        expected = spearmanr(a[footprint], b[footprint]).statistic
        actual = binary_rank_correlation(a, b, footprint)
        if np.isnan(expected):
            assert actual is None
        else:
            assert actual == pytest.approx(expected, abs=1e-12)
    assert binary_rank_correlation(np.zeros((2, 2), bool), np.ones((2, 2), bool), np.ones((2, 2), bool)) is None
    with pytest.raises(ValueError):
        binary_rank_correlation(np.zeros((2, 2), bool), np.ones((2, 2), bool), np.zeros((2, 2), bool))


def test_overlap_radius_is_euclidean_and_directional():
    prior = np.zeros((11, 11)); prior[5, 5] = 1
    mine = np.zeros_like(prior); mine[5, 8] = 1; mine[0, 0] = 1
    near = uniqueness._near(prior > 0)
    assert near[5, 8] and near[7, 7]  # radius 3 px is inclusive
    assert not near[6, 8] and not near[5, 9]
    assert uniqueness.dot_overlap(mine, prior) == .5
    assert uniqueness.dot_overlap(prior, mine) == 1.0


def test_lattice_pigeonhole_bound():
    footprint = np.ones((11, 11), bool)
    lattice = np.zeros_like(footprint); lattice[5, 5] = 1
    covered = uniqueness._near(lattice) & footprint
    uncovered = int((footprint & ~covered).sum())
    rng = np.random.default_rng(2026)
    for count in (1, 20, uncovered, uncovered + 1, footprint.size):
        candidate = np.zeros(footprint.size, bool)
        candidate[rng.choice(footprint.size, count, replace=False)] = True
        actual = covered.ravel()[candidate].mean()
        assert actual + 1e-12 >= lower_overlap_bound(count, uncovered)
    assert lower_overlap_bound(37654, 6649) == pytest.approx(.8234184947150369)
    with pytest.raises(ValueError):
        lower_overlap_bound(0, 1)
    with pytest.raises(ValueError):
        lower_overlap_bound(1, -1)


@pytest.mark.parametrize("seed", range(8))
def test_shared_soft_metric_matches_literal_equations(seed):
    rng = np.random.default_rng(seed)
    pred = rng.choice([0., 0., 0., .2, .7, 1.], size=(7, 8))
    truth = rng.random(pred.shape) < .1
    exact, literal = metric.dti_exact(pred, truth), metric.dti_bruteforce(pred, truth)
    for key in ("tp", "fp", "fn", "dti"):
        assert exact[key] == pytest.approx(literal[key], abs=1e-10)


def test_binary_and_soft_metrics_agree_with_exact_masking():
    pred = np.zeros((6, 6)); pred[2, 2] = pred[4, 4] = 1
    truth = np.zeros_like(pred, dtype=bool); truth[2, 3] = truth[4, 4] = True
    known = np.zeros_like(truth); known[4, 4] = True
    valid = np.ones_like(truth)
    binary = metric.dti_binary(pred > 0, truth, valid, known)
    exact = metric.dti_exact(pred, truth, valid, known)
    for key in ("tp", "fp", "fn", "dti"):
        assert exact[key] == pytest.approx(binary[key], abs=1e-12)
    # With no truth, all positive mass is still false-positive mass.
    assert metric.dti_exact(pred, np.zeros_like(truth))["fp"] == 2


def test_metric_prose_counterexample_one_dot_covers_two_truth_cells():
    truth = np.zeros((5, 5), bool); truth[2, 1] = truth[2, 3] = True
    pred = np.zeros((5, 5)); pred[2, 2] = 1
    measured = metric.dti_exact(pred, truth)
    dot_self_credit = float(metric.kernel(1))
    assert measured["tp"] == pytest.approx(2 * dot_self_credit)
    assert measured["tp"] > dot_self_credit  # disputed upstream prose, not arithmetic
