# Implementation guide: see docs/plans/LEVEL-2-MLOPS.md — "Monitoring & Drift Detection" section
"""
Model prediction drift detection for Saudi Sentinel AI pipelines.

Drift detection strategy: Population Stability Index (PSI) over a 30-day rolling baseline.
PSI thresholds (from plan doc):
  PSI < 0.1:  No significant drift (stable)
  PSI ≥ 0.1:  Moderate drift → WARNING alert
  PSI ≥ 0.2:  Significant drift → CRITICAL alert → trigger retraining

Additional monitoring metrics (from docs/plans/LEVEL-2-MLOPS.md — "What to Monitor"):
  Data:   New tiles received per AOI per week (< 1 = pipeline failure)
  Data:   Cloud coverage % (> 80% for 3 consecutive = alert)
  Model:  % high-confidence predictions (drop > 15% = alert)
  Model:  Inference latency p95 (> 200ms = alert)
  System: API error rate (> 5% = alert)
  Business: Change detection area spike (10× normal = likely error)

See: docs/plans/LEVEL-2-MLOPS.md — "Monitoring & Drift Detection"
"""

from __future__ import annotations

from typing import Optional

import numpy as np


class DriftDetector:
    """
    Detects prediction distribution drift using PSI (Population Stability Index).

    Implementation guide: docs/plans/LEVEL-2-MLOPS.md — "Drift Detection Strategy"

    Usage:
        detector = DriftDetector(project="urban-sprawl", baseline_days=30)
        detector.check_prediction_drift("urban-sprawl", new_predictions)
    """

    def __init__(self, project: str, baseline_days: int = 30) -> None:
        self.project = project
        self.baseline_days = baseline_days

    def check_prediction_drift(
        self,
        project: str,
        new_predictions: np.ndarray,
    ) -> float:
        """
        Compare new prediction distribution against rolling baseline using PSI.

        Args:
            project:         Project name (used to query historical predictions)
            new_predictions: Latest prediction array (probabilities or class indices)

        Returns:
            PSI value. Triggers alert if PSI > 0.1.

        Implementation:
        1. Fetch 30-day baseline predictions from PostGIS predictions table
        2. Compute PSI: sum((expected_pct - actual_pct) * ln(expected_pct / actual_pct))
        3. If PSI > 0.2: call self.alert(project, "CRITICAL", ...)
        4. If PSI > 0.1: call self.alert(project, "WARNING", ...)
        5. Return PSI value
        """
        raise NotImplementedError(
            "Implement PSI computation. See docs/plans/LEVEL-2-MLOPS.md — 'Drift Detection Strategy'."
        )

    def compute_psi(
        self,
        baseline: np.ndarray,
        new_data: np.ndarray,
        n_bins: int = 10,
        epsilon: float = 1e-6,
    ) -> float:
        """
        Population Stability Index between baseline and new distributions.

        PSI = Σ (actual_pct - expected_pct) × ln(actual_pct / expected_pct)

        Args:
            baseline: Historical prediction array (30-day window)
            new_data: Current batch predictions
            n_bins:   Number of histogram bins
            epsilon:  Small value to avoid log(0)

        Returns:
            PSI score (float). 0 = identical distributions.
        """
        raise NotImplementedError

    def get_baseline_distribution(self, project: str, days: int = 30) -> np.ndarray:
        """
        Fetch historical predictions from PostGIS for baseline computation.

        Queries the predictions table for the last N days of predictions
        for this project. Returns flattened prediction probability array.
        """
        raise NotImplementedError

    def alert(self, project: str, severity: str, message: str) -> None:
        """
        Push drift alert to the alert system.

        Implementation:
        - INSERT INTO alerts (project_name, alert_type, severity, message, ...)
        - Push to Redis pub/sub for WebSocket delivery
        - If CRITICAL: trigger retraining DAG via Airflow REST API
        """
        raise NotImplementedError

    def check_data_pipeline_health(self, aoi_id: str, sensor: str) -> dict:
        """
        Check if data pipeline is delivering new tiles as expected.

        Alert if: fewer than 1 tile per week received for any AOI.

        Returns:
            Health status dict: {status, tiles_last_7d, expected_tiles, alert_triggered}
        """
        raise NotImplementedError
