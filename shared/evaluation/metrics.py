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
    p = (pred >= threshold).astype(bool).ravel()
    t = (target >= threshold).astype(bool).ravel()

    if class_idx == 1:
        intersection = np.sum(p & t)
        union = np.sum(p | t)
    else:
        intersection = np.sum(~p & ~t)
        union = np.sum(~p | ~t)

    if union == 0:
        return 0.0
    return float(intersection / union)


def f1_score(
    pred: np.ndarray,
    target: np.ndarray,
    threshold: float = 0.5,
) -> float:
    """F1 = 2 × (precision × recall) / (precision + recall)."""
    p, r = precision_recall(pred, target, threshold)
    if p + r == 0:
        return 0.0
    return float(2.0 * p * r / (p + r))


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
    p = (pred >= threshold).astype(bool).ravel()
    t = (target >= threshold).astype(bool).ravel()

    tp = np.sum(p & t)
    fp = np.sum(p & ~t)
    fn = np.sum(~p & t)

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    return (precision, recall)


def false_alarm_rate(pred: np.ndarray, target: np.ndarray, threshold: float = 0.5) -> float:
    """
    FAR = FP / (FP + TN) — fraction of negative pixels wrongly flagged.
    Critical for oil spill and urban sprawl detection (too many false alarms = unusable system).
    Target: < 0.15 for urban sprawl, < 0.40 for oil spill.
    """
    p = (pred >= threshold).astype(bool).ravel()
    t = (target >= threshold).astype(bool).ravel()

    fp = np.sum(p & ~t)
    tn = np.sum(~p & ~t)

    if (fp + tn) == 0:
        return 0.0
    return float(fp / (fp + tn))


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
    if n_classes == 2:
        p = (pred >= threshold).astype(int).ravel()
        t = (target >= threshold).astype(int).ravel()
    else:
        p = pred.astype(int).ravel()
        t = target.astype(int).ravel()

    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for true_val, pred_val in zip(t, p):
        if 0 <= true_val < n_classes and 0 <= pred_val < n_classes:
            cm[true_val, pred_val] += 1
    return cm


def overall_accuracy(pred: np.ndarray, target: np.ndarray) -> float:
    """Overall accuracy = (TP + TN) / total pixels."""
    p = pred.ravel()
    t = target.ravel()
    total = t.size
    if total == 0:
        return 0.0
    return float(np.sum(p == t) / total)


def cohens_kappa(confusion_mat: np.ndarray) -> float:
    """
    Cohen's Kappa — agreement beyond chance.
    κ = (p_o - p_e) / (1 - p_e)
    κ > 0.70 is target for crop type mapping (Project 03).
    """
    cm = confusion_mat.astype(np.float64)
    total = cm.sum()
    if total == 0:
        return 0.0

    p_o = np.trace(cm) / total
    row_sums = cm.sum(axis=1)
    col_sums = cm.sum(axis=0)
    p_e = np.sum(row_sums * col_sums) / (total * total)

    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0
    return float((p_o - p_e) / (1.0 - p_e))


def mean_absolute_error(pred: np.ndarray, target: np.ndarray) -> float:
    """MAE for regression tasks (e.g. dune displacement prediction, Project 07)."""
    return float(np.mean(np.abs(pred.ravel() - target.ravel())))


def auc_roc(scores: np.ndarray, labels: np.ndarray) -> float:
    """
    Area under the ROC curve for binary classification.
    Target: > 0.83 for desertification (Project 05), > 0.82 for flood risk (Project 08).
    """
    s = scores.ravel().astype(np.float64)
    l = labels.ravel().astype(np.float64)

    desc_order = np.argsort(-s)
    s = s[desc_order]
    l = l[desc_order]

    total_pos = np.sum(l == 1)
    total_neg = np.sum(l == 0)

    if total_pos == 0 or total_neg == 0:
        return 0.0

    tpr_prev = 0.0
    fpr_prev = 0.0
    tp = 0.0
    fp = 0.0
    auc = 0.0

    for i in range(len(s)):
        if l[i] == 1:
            tp += 1
        else:
            fp += 1
        tpr = tp / total_pos
        fpr = fp / total_neg
        auc += 0.5 * (tpr + tpr_prev) * (fpr - fpr_prev)
        tpr_prev = tpr
        fpr_prev = fpr

    return float(auc)


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
    p = pred.astype(int).ravel()
    t = target.astype(int).ravel()
    result = {}

    for c in range(n_classes):
        tp = np.sum((p == c) & (t == c))
        fp = np.sum((p == c) & (t != c))
        fn = np.sum((p != c) & (t == c))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        result[c] = float(2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    return result
