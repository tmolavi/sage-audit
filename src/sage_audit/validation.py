"""Empirical validation and calibration framework for SAGE & Citation Survival Proxy (CSP).

Provides statistical tools to validate SAGE and CSP scores against empirical AI observation datasets:
- Spearman rank correlation (rho, p-value)
- Area Under the ROC Curve (AUROC / ROC-AUC)
- Precision@k
- Brier score (mean squared calibration error)
- Calibration bins analysis (predicted vs observed citation rates)

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence
from pydantic import BaseModel, Field


class CalibrationBin(BaseModel):
    """A single calibration bin comparing predicted probability to observed frequency."""

    bin_label: str = Field(description="Bin interval range label, e.g. '0-20%'.")
    min_val: float = Field(ge=0.0, le=1.0)
    max_val: float = Field(ge=0.0, le=1.0)
    sample_count: int = Field(ge=0, description="Total observations in this bin.")
    mean_predicted: Optional[float] = Field(default=None, description="Average predicted probability in this bin.")
    observed_rate: Optional[float] = Field(default=None, description="Observed empirical citation rate (positive fraction).")


class ValidationResult(BaseModel):
    """Structured evaluation report comparing SAGE / CSP scores against real observed outcomes."""

    sample_size: int = Field(ge=0, description="Number of evaluated samples.")
    validation_status: str = Field(description="'validated' if samples > 0 else 'unvalidated'")
    dataset_name: Optional[str] = Field(default=None, description="Identifier of the empirical benchmark dataset.")
    spearman_rho: Optional[float] = Field(default=None, description="Spearman rank correlation coefficient (-1.0 to 1.0).")
    spearman_p_value: Optional[float] = Field(default=None, description="Two-tailed p-value for Spearman correlation.")
    auroc: Optional[float] = Field(default=None, description="Area under the ROC curve (0.0 to 1.0; 0.5 = random).")
    precision_at_k: Optional[float] = Field(default=None, description="Precision for top-k predicted items.")
    k: int = Field(default=5, description="Cutoff k used for Precision@k.")
    brier_score: Optional[float] = Field(default=None, description="Brier score: mean squared error between prediction and binary outcome (0.0 = perfect).")
    calibration_bins: list[CalibrationBin] = Field(default_factory=list, description="Binned calibration curve breakdown.")
    methodology_notes: list[str] = Field(default_factory=list, description="Methodological caveats and interpretation notes.")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def _rank_data(values: Sequence[float]) -> list[float]:
    """Assign fractional ranks to elements (1-based), properly handling ties."""
    n = len(values)
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n
    
    i = 0
    while i < n:
        j = i
        while j < n - 1 and indexed[j + 1][1] == indexed[j][1]:
            j += 1
        # Assign average rank to tied values
        avg_rank = 1.0 + (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_rank_correlation(
    x: Sequence[float], y: Sequence[float]
) -> tuple[Optional[float], Optional[float]]:
    """Compute Spearman's rank correlation coefficient (rho) and asymptotic two-tailed p-value.
    
    Returns (rho, p_value). Returns (None, None) if sample size < 3 or variance is zero.
    """
    n = len(x)
    if n != len(y) or n < 3:
        return None, None

    rank_x = _rank_data(x)
    rank_y = _rank_data(y)

    mean_rx = sum(rank_x) / n
    mean_ry = sum(rank_y) / n

    num = sum((rx - mean_rx) * (ry - mean_ry) for rx, ry in zip(rank_x, rank_y))
    den_x = math.sqrt(sum((rx - mean_rx) ** 2 for rx in rank_x))
    den_y = math.sqrt(sum((ry - mean_ry) ** 2 for ry in rank_y))

    if den_x == 0.0 or den_y == 0.0:
        return 0.0, 1.0

    rho = num / (den_x * den_y)
    rho = max(-1.0, min(1.0, rho))

    # Asymptotic t-distribution p-value approximation
    if abs(rho) >= 1.0:
        p_val = 0.0
    else:
        t_stat = rho * math.sqrt((n - 2) / (1.0 - rho ** 2))
        # Simple asymptotic normal approximation for df >= 10, or standard error approximation
        # For general usage without heavy scipy dependency:
        # Standard error = 1 / sqrt(n - 1)
        z = abs(t_stat)
        # Erf-based two-tailed normal approximation
        p_val = math.erfc(z / math.sqrt(2.0))
        p_val = max(0.0, min(1.0, p_val))

    return round(rho, 4), round(p_val, 4)


def roc_auc_score(y_true: Sequence[int | float | bool], y_score: Sequence[float]) -> Optional[float]:
    """Compute Area Under the Receiver Operating Characteristic Curve (AUROC) via Mann-Whitney U.
    
    y_true: Binary ground truth (0/1, False/True).
    y_score: Continuous predicted score or probability.
    """
    n = len(y_true)
    if n != len(y_score) or n == 0:
        return None

    binary_true = [1 if val else 0 for val in y_true]
    n_pos = sum(binary_true)
    n_neg = n - n_pos

    if n_pos == 0 or n_neg == 0:
        return None  # Cannot compute AUROC with only one class

    ranks = _rank_data(y_score)
    sum_ranks_pos = sum(r for r, y in zip(ranks, binary_true) if y == 1)

    # Mann-Whitney U statistic for positive class
    u_stat = sum_ranks_pos - (n_pos * (n_pos + 1)) / 2.0
    auc = u_stat / (n_pos * n_neg)
    return round(max(0.0, min(1.0, auc)), 4)


def precision_at_k(
    y_true: Sequence[int | float | bool], y_score: Sequence[float], k: int = 5
) -> Optional[float]:
    """Compute Precision@k for ranked predictions against binary ground truth."""
    n = len(y_true)
    if n != len(y_score) or n == 0 or k <= 0:
        return None

    binary_true = [1 if val else 0 for val in y_true]
    actual_k = min(k, n)

    # Sort descending by predicted score
    order = sorted(range(n), key=lambda i: y_score[i], reverse=True)
    top_k_indices = order[:actual_k]

    pos_in_top_k = sum(binary_true[i] for i in top_k_indices)
    return round(pos_in_top_k / actual_k, 4)


def brier_score(y_true: Sequence[int | float | bool], y_prob: Sequence[float]) -> Optional[float]:
    """Compute Brier score (mean squared error between predicted probability [0, 1] and binary outcome)."""
    n = len(y_true)
    if n != len(y_prob) or n == 0:
        return None

    binary_true = [1.0 if val else 0.0 for val in y_true]
    mse = sum((prob - true) ** 2 for prob, true in zip(y_prob, binary_true)) / n
    return round(mse, 4)


def calibration_curve_bins(
    y_true: Sequence[int | float | bool],
    y_prob: Sequence[float],
    bin_intervals: Optional[list[tuple[float, float, str]]] = None,
) -> list[CalibrationBin]:
    """Breakdown predictions into probability bins to inspect empirical calibration curve."""
    if bin_intervals is None:
        bin_intervals = [
            (0.0, 0.20, "0-20%"),
            (0.20, 0.40, "20-40%"),
            (0.40, 0.60, "40-60%"),
            (0.60, 0.80, "60-80%"),
            (0.80, 1.0001, "80-100%"),
        ]

    binary_true = [1.0 if val else 0.0 for val in y_true]
    bins: list[CalibrationBin] = []

    for low, high, label in bin_intervals:
        bin_probs = [p for p in y_prob if low <= p < high]
        bin_trues = [t for p, t in zip(y_prob, binary_true) if low <= p < high]

        count = len(bin_probs)
        mean_p = round(sum(bin_probs) / count, 4) if count > 0 else None
        obs_rate = round(sum(bin_trues) / count, 4) if count > 0 else None

        bins.append(
            CalibrationBin(
                bin_label=label,
                min_val=low,
                max_val=min(1.0, high),
                sample_count=count,
                mean_predicted=mean_p,
                observed_rate=obs_rate,
            )
        )
    return bins


def evaluate_sage_vs_observed(
    predictions: Sequence[float],
    observations: Sequence[int | float | bool],
    k: int = 5,
    dataset_name: Optional[str] = None,
    normalize_scores: bool = True,
) -> ValidationResult:
    """Validate SAGE or CSP scores against real observed AI search citation outcomes.
    
    Parameters
    ----------
    predictions: Continuous SAGE scores (0-100) or CSP scores.
    observations: Binary or continuous citation outcomes (1 = cited, 0 = not cited).
    k: Top-k ranking cutoff for Precision@k.
    dataset_name: Optional label of the benchmark corpus.
    normalize_scores: If True and scores are in 0-100 scale, scales to [0, 1] for Brier/bins.
    """
    n = len(predictions)
    if n == 0 or n != len(observations):
        return ValidationResult(
            sample_size=0,
            validation_status="unvalidated",
            dataset_name=dataset_name,
            methodology_notes=["No evaluation data provided or mismatched array lengths."],
        )

    # Normalize 0-100 scores to 0-1 for probability evaluation if needed
    max_p = max(predictions) if predictions else 0.0
    if normalize_scores and max_p > 1.0:
        probs = [max(0.0, min(1.0, p / 100.0)) for p in predictions]
    else:
        probs = [max(0.0, min(1.0, p)) for p in predictions]

    rho, p_val = spearman_rank_correlation(predictions, observations)
    auc = roc_auc_score(observations, predictions)
    prec_k = precision_at_k(observations, predictions, k=k)
    brier = brier_score(observations, probs)
    cal_bins = calibration_curve_bins(observations, probs)

    notes = [
        "SAGE/CSP scores evaluate static retrieval-readiness and semantic extractability.",
        "Observed citation outcomes reflect live AI model generation and search grounding.",
        "Spearman rho assesses monotonic ranking alignment.",
        "AUROC measures discriminatory ability to separate cited from non-cited pages.",
        "Brier score and calibration bins assess whether score magnitudes match empirical citation rates.",
    ]

    return ValidationResult(
        sample_size=n,
        validation_status="validated" if n >= 5 else "preliminary",
        dataset_name=dataset_name,
        spearman_rho=rho,
        spearman_p_value=p_val,
        auroc=auc,
        precision_at_k=prec_k,
        k=k,
        brier_score=brier,
        calibration_bins=cal_bins,
        methodology_notes=notes,
    )
