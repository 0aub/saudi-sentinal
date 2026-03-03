# Implementation guide: see docs/plans/level-1-notebooks/ — "Evaluation Metrics" sections in each notebook plan
"""
Shared evaluation metrics for all 9 Saudi Sentinel AI projects.

Each project has specific target metrics (see individual notebook plans),
but the underlying computation functions are shared here.

Metric coverage:
  Segmentation:  IoU, F1, precision, recall, FAR            [Projects 01, 06, 07, 09]
  Classification: Overall accuracy, per-class F1, kappa     [Projects 03, 04, 05, 08]
  Time-series:   Trend accuracy, R², Moran's I              [Projects 02, 04]
  Regression:    MAE, RMSE                                  [Project 07 — displacement]
  Ranking:       AUC-ROC                                    [Projects 05, 08]

See: docs/plans/level-1-notebooks/ — "Evaluation Metrics" tables in each notebook plan
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


def iou(
    pred: np.ndarray,
    target: np.ndarray,
    threshold: float = 0.5,
    class_idx: int = 1,
) -> float:
    """
    Intersection-over-Union for a single class.

    Args:
        pred:      Predicted probabilities or logits, any shape
        target:    Ground truth binary mask, same shape
        threshold: Binarization threshold (default 0.5)
        class_idx: Which class to compute IoU for (1 = positive/changed class)

    Returns:
        IoU ∈ [0, 1]. Returns 0.0 if class is absent in both pred and target.
    """
    raise NotImplementedError


def f1_score(
    pred: np.ndarray,
    target: np.ndarray,
    threshold: float = 0.5,
) -> float:
    """F1 = 2 × (precision × recall) / (precision + recall)."""
    raise NotImplementedError


def precision_recall(
    pred: np.ndarray,
    target: np.ndarray,
    threshold: float = 0.5,
) -> tuple:
    """
    Compute precision and recall for binary classification.

    Returns:
        (precision, recall) both in [0, 1]
    """
    raise NotImplementedError


def false_alarm_rate(pred: np.ndarray, target: np.ndarray, threshold: float = 0.5) -> float:
    """
    FAR = FP / (FP + TN) — fraction of negative pixels wrongly flagged.
    Critical for oil spill and urban sprawl detection (too many false alarms = unusable system).
    Target: < 0.15 for urban sprawl, < 0.40 for oil spill.
    """
    raise NotImplementedError


def confusion_matrix(
    pred: np.ndarray,
    target: np.ndarray,
    n_classes: int,
    threshold: float = 0.5,
) -> np.ndarray:
    """
    Compute confusion matrix for multi-class or binary classification.

    Returns:
        Integer array of shape (n_classes, n_classes):
          rows = true class, columns = predicted class
    """
    raise NotImplementedError


def overall_accuracy(pred: np.ndarray, target: np.ndarray) -> float:
    """Overall accuracy = (TP + TN) / total pixels."""
    raise NotImplementedError


def cohens_kappa(confusion_mat: np.ndarray) -> float:
    """
    Cohen's Kappa — agreement beyond chance.
    κ = (p_o - p_e) / (1 - p_e)
    κ > 0.70 is target for crop type mapping (Project 03).
    """
    raise NotImplementedError


def mean_absolute_error(pred: np.ndarray, target: np.ndarray) -> float:
    """MAE for regression tasks (e.g. dune displacement prediction, Project 07)."""
    raise NotImplementedError


def auc_roc(scores: np.ndarray, labels: np.ndarray) -> float:
    """
    Area under the ROC curve for binary classification.
    Target: > 0.83 for desertification (Project 05), > 0.82 for flood risk (Project 08).
    """
    raise NotImplementedError


def per_class_f1(
    pred: np.ndarray,
    target: np.ndarray,
    n_classes: int,
) -> Dict[int, float]:
    """
    Compute F1 score for each class independently.

    Returns:
        Dict mapping class_index → F1 score.
        Used for per-class evaluation in crop type mapping (Project 03).
    """
    raise NotImplementedError
