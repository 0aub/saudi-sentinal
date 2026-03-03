# Implementation guide: see docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — "Evaluation Metrics"
"""
Evaluation metrics for binary change detection (urban sprawl).

Target metrics (from plan doc):
  IoU (change class):   > 0.65   Primary metric
  F1-score:             > 0.70
  Precision:            > 0.75   Avoid false positives (sand flagged as construction)
  Recall:               > 0.65
  FAR (False Alarm Rate): < 0.15  Critical for production usability

See: docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — "Evaluation Metrics"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import torch


@dataclass
class ChangeDetectionMetrics:
    """Computed evaluation metrics for a single evaluation run."""
    iou: float
    f1: float
    precision: float
    recall: float
    false_alarm_rate: float    # FAR = FP / (FP + TN)
    confusion_matrix: np.ndarray  # shape (2, 2): [[TN, FP], [FN, TP]]


def compute_iou(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """
    Compute Intersection-over-Union for the change class.

    Args:
        pred:      Predicted logits or probabilities, shape (N, 1, H, W)
        target:    Ground truth binary mask, shape (N, 1, H, W)
        threshold: Classification threshold (default 0.5)

    Returns:
        IoU score for the "changed" class (float in [0, 1]).
    """
    raise NotImplementedError


def compute_all_metrics(
    pred: torch.Tensor,
    target: torch.Tensor,
    threshold: float = 0.5,
) -> ChangeDetectionMetrics:
    """
    Compute IoU, F1, precision, recall, and FAR in one pass.

    Implementation notes:
    - Binarize predictions at threshold
    - Compute TP, FP, TN, FN from flattened tensors
    - FAR = FP / (FP + TN)  (fraction of truly unchanged pixels wrongly flagged)
    """
    raise NotImplementedError


def per_aoi_metrics(
    predictions: Dict[str, torch.Tensor],
    targets: Dict[str, torch.Tensor],
) -> Dict[str, ChangeDetectionMetrics]:
    """
    Compute metrics separately for each AOI (riyadh, jeddah, dammam).

    Returns:
        Dict mapping aoi_id → ChangeDetectionMetrics
    """
    raise NotImplementedError
