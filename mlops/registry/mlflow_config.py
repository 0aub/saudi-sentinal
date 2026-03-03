# Implementation guide: see docs/plans/LEVEL-2-MLOPS.md — "MLflow Integration" section
"""
MLflow experiment structure and logging helpers for Saudi Sentinel AI.

MLflow experiment structure (from plan doc):
  urban-sprawl-detector/
  green-riyadh-monitor/
  crop-type-mapping/
  groundwater-depletion/
  desertification-warning/
  neom-construction-tracker/
  dune-migration-predictor/
  flash-flood-risk/
  oil-spill-detection/

Model registry stages:
  None → Staging → Production → Archived

Promotion rules:
  Staging → Production:
    - val_iou > 0.65 (project-specific threshold — see each notebook plan)
    - Inference time < 100ms per chip
    - Shadow deployment for 2 weeks without regression
    - Human approval for yellow-light projects (06-09)

See: docs/plans/LEVEL-2-MLOPS.md — "MLflow Integration"
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

MLFLOW_EXPERIMENTS = {
    "urban-sprawl":    "urban-sprawl-detector",
    "green-riyadh":    "green-riyadh-monitor",
    "crop-mapping":    "crop-type-mapping",
    "groundwater":     "groundwater-depletion",
    "desertification": "desertification-warning",
    "neom-tracker":    "neom-construction-tracker",
    "dune-migration":  "dune-migration-predictor",
    "flash-flood":     "flash-flood-risk",
    "oil-spill":       "oil-spill-detection",
}

# Per-project promotion thresholds (from individual notebook plans)
PROMOTION_THRESHOLDS = {
    "urban-sprawl":    {"val_iou": 0.65, "val_f1": 0.70},
    "green-riyadh":    {"vegetation_accuracy": 0.85, "trend_precision": 0.80},
    "crop-mapping":    {"overall_accuracy": 0.78, "wheat_f1": 0.85},
    "groundwater":     {"farm_detection_accuracy": 0.90, "change_precision": 0.85},
    "desertification": {"auc_roc": 0.83, "high_risk_f1": 0.75},
    "neom-tracker":    {"overall_accuracy": 0.70, "cleared_iou": 0.65},
    "dune-migration":  {"displacement_mae_m": 8.0},  # lower is better
    "flash-flood":     {"auc_roc": 0.82, "high_risk_precision": 0.75},
    "oil-spill":       {"stage1_recall": 0.90, "stage2_precision_oil": 0.60},
}


def setup_mlflow(tracking_uri: Optional[str] = None) -> None:
    """
    Initialize MLflow client and create all experiments if they don't exist.

    Args:
        tracking_uri: MLflow server URL. Falls back to MLFLOW_TRACKING_URI env var.

    Implementation:
    - mlflow.set_tracking_uri(tracking_uri or os.environ["MLFLOW_TRACKING_URI"])
    - For each experiment in MLFLOW_EXPERIMENTS.values():
        mlflow.create_experiment(name) if not exists
    """
    raise NotImplementedError(
        "Set up MLflow client and create experiments. See docs/plans/LEVEL-2-MLOPS.md."
    )


def log_training_run(
    project: str,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    model_path: str,
    artifacts: Optional[list] = None,
) -> str:
    """
    Log a training run to MLflow with params, metrics, and model artifact.

    Args:
        project:    Project name (must be key in MLFLOW_EXPERIMENTS)
        params:     Hyperparameters dict (model, backbone, lr, batch_size, etc.)
        metrics:    Evaluation metrics dict (val_iou, val_f1, inference_time_ms, etc.)
        model_path: Path to saved ONNX model
        artifacts:  Optional list of artifact paths (plots, confusion matrix, etc.)

    Returns:
        MLflow run_id for the logged run.

    See: docs/plans/LEVEL-2-MLOPS.md — "What Gets Logged Per Run" code sample
    """
    raise NotImplementedError(
        "Implement MLflow run logging. See docs/plans/LEVEL-2-MLOPS.md — 'What Gets Logged'."
    )


def promote_model(
    project: str,
    run_id: str,
    from_stage: str = "None",
    to_stage: str = "Staging",
) -> None:
    """
    Promote a model version in the MLflow registry.

    Validates promotion thresholds before promoting to Production.
    Yellow-light projects (06-09) require additional human approval flag.

    See: docs/plans/LEVEL-2-MLOPS.md — "Model Registry Stages → Promotion rules"
    """
    raise NotImplementedError(
        "Implement model promotion with threshold validation. "
        "See docs/plans/LEVEL-2-MLOPS.md — 'Model Registry Stages'."
    )
