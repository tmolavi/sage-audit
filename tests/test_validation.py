"""Tests for SAGE empirical validation and calibration module.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import math
import pytest
from sage_audit.validation import (
    brier_score,
    calibration_curve_bins,
    evaluate_sage_vs_observed,
    precision_at_k,
    roc_auc_score,
    spearman_rank_correlation,
)


def test_spearman_rank_correlation_perfect_and_inverse():
    x = [10.0, 20.0, 30.0, 40.0, 50.0]
    y_perfect = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_inverse = [5.0, 4.0, 3.0, 2.0, 1.0]

    rho_perf, p_perf = spearman_rank_correlation(x, y_perfect)
    assert rho_perf == pytest.approx(1.0)
    assert p_perf == pytest.approx(0.0, abs=1e-3)

    rho_inv, p_inv = spearman_rank_correlation(x, y_inverse)
    assert rho_inv == pytest.approx(-1.0)
    assert p_inv == pytest.approx(0.0, abs=1e-3)


def test_spearman_with_ties():
    x = [10.0, 20.0, 20.0, 40.0, 50.0]
    y = [1.0, 2.0, 3.0, 4.0, 5.0]
    rho, p_val = spearman_rank_correlation(x, y)
    assert rho is not None
    assert 0.9 <= rho <= 1.0


def test_roc_auc_score():
    y_true = [0, 0, 0, 1, 1, 1]
    y_perfect = [10.0, 20.0, 30.0, 70.0, 80.0, 90.0]
    y_worst = [90.0, 80.0, 70.0, 30.0, 20.0, 10.0]

    auc_perf = roc_auc_score(y_true, y_perfect)
    assert auc_perf == pytest.approx(1.0)

    auc_worst = roc_auc_score(y_true, y_worst)
    assert auc_worst == pytest.approx(0.0)

    # Empty or single class returns None
    assert roc_auc_score([1, 1, 1], [10.0, 20.0, 30.0]) is None


def test_precision_at_k():
    y_true = [1, 0, 1, 1, 0, 0]
    y_scores = [90.0, 80.0, 70.0, 60.0, 50.0, 40.0]

    # Top 3 are indices 0, 1, 2 with true labels 1, 0, 1 -> 2/3
    prec = precision_at_k(y_true, y_scores, k=3)
    assert prec == pytest.approx(2.0 / 3.0, abs=1e-4)


def test_brier_score():
    y_true = [1, 0, 1, 0]
    y_perfect = [1.0, 0.0, 1.0, 0.0]
    y_worst = [0.0, 1.0, 0.0, 1.0]

    assert brier_score(y_true, y_perfect) == pytest.approx(0.0)
    assert brier_score(y_true, y_worst) == pytest.approx(1.0)


def test_calibration_curve_bins():
    y_true = [0, 0, 1, 1, 1]
    y_prob = [0.10, 0.15, 0.45, 0.70, 0.90]

    bins = calibration_curve_bins(y_true, y_prob)
    assert len(bins) == 5

    bin_0_20 = bins[0]
    assert bin_0_20.bin_label == "0-20%"
    assert bin_0_20.sample_count == 2
    assert bin_0_20.mean_predicted == pytest.approx(0.125)
    assert bin_0_20.observed_rate == pytest.approx(0.0)


def test_evaluate_sage_vs_observed_end_to_end():
    preds = [25.0, 45.0, 65.0, 80.0, 85.0, 92.0]
    obs = [0, 0, 1, 0, 1, 1]

    res = evaluate_sage_vs_observed(preds, obs, k=3, dataset_name="synthetic-rag-benchmark")
    assert res.validation_status == "validated"
    assert res.sample_size == 6
    assert res.dataset_name == "synthetic-rag-benchmark"
    assert res.spearman_rho is not None
    assert res.auroc is not None
    assert res.precision_at_k is not None
    assert res.brier_score is not None
    assert len(res.calibration_bins) == 5
    assert len(res.methodology_notes) > 0
