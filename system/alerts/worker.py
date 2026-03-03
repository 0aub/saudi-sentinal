# Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "Alert Worker"
"""
Alert worker — runs continuously, polls PostGIS, evaluates rules, pushes alerts.

Architecture:
  - Polls PostGIS predictions table every 60 seconds for unprocessed predictions
  - Evaluates ALERT_RULES for each new prediction
  - Stores triggered alerts in PostGIS alerts table
  - Pushes to Redis pub/sub for WebSocket delivery to React frontend
  - Sends email for CRITICAL severity alerts

Run with:
  python system/alerts/worker.py

Or via Docker Compose service "alert-worker".
See: docs/plans/LEVEL-3-SYSTEM.md — "Alert Worker"
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from system.alerts.rules import ALERT_RULES

logger = logging.getLogger(__name__)


class AlertWorker:
    """
    Continuously polls for new model predictions and evaluates alert rules.

    Implementation guide: docs/plans/LEVEL-3-SYSTEM.md — "Alert Worker" code block
    """

    def __init__(
        self,
        poll_interval_seconds: int = 60,
        database_url: str | None = None,
        redis_url: str | None = None,
    ) -> None:
        self.poll_interval = poll_interval_seconds
        raise NotImplementedError(
            "Initialize DB connection and Redis client. "
            "See docs/plans/LEVEL-3-SYSTEM.md — AlertWorker."
        )

    async def run(self) -> None:
        """Main loop — runs indefinitely."""
        logger.info("Alert worker started. Polling every %ds.", self.poll_interval)
        while True:
            try:
                for project in ALERT_RULES:
                    new_predictions = await self.get_unprocessed_predictions(project)
                    for pred in new_predictions:
                        alerts = self.evaluate_rules(project, pred)
                        for alert in alerts:
                            await self.store_alert(alert)
                            await self.push_to_websocket(alert)
                            if alert.get("severity") == "critical":
                                await self.send_email(alert)
                    await self.mark_predictions_processed(project, new_predictions)
            except Exception as e:
                logger.error("Alert worker error: %s", e, exc_info=True)

            await asyncio.sleep(self.poll_interval)

    async def get_unprocessed_predictions(self, project: str) -> List[Dict]:
        """Query predictions table for rows not yet evaluated by alert worker."""
        raise NotImplementedError

    def evaluate_rules(self, project: str, prediction: Dict) -> List[Dict]:
        """
        Evaluate all ALERT_RULES for a project against a prediction summary.

        Args:
            project:    Project name key in ALERT_RULES
            prediction: Dict from predictions table (includes summary_stats JSONB)

        Returns:
            List of alert dicts to be stored and pushed.

        Implementation:
        - Extract summary_stats from prediction
        - For each rule, eval(rule["condition"], summary_stats)
        - If condition is True, build alert dict from rule["message"].format(**summary_stats)
        """
        raise NotImplementedError

    async def store_alert(self, alert: Dict) -> None:
        """INSERT INTO alerts table."""
        raise NotImplementedError

    async def push_to_websocket(self, alert: Dict) -> None:
        """Publish alert to Redis pub/sub channel 'alerts'."""
        raise NotImplementedError

    async def send_email(self, alert: Dict) -> None:
        """Send email notification for CRITICAL alerts."""
        raise NotImplementedError

    async def mark_predictions_processed(self, project: str, predictions: List[Dict]) -> None:
        """Mark predictions as processed to avoid re-evaluation."""
        raise NotImplementedError


if __name__ == "__main__":
    import os
    worker = AlertWorker(
        database_url=os.environ["DATABASE_URL"],
        redis_url=os.environ["REDIS_URL"],
    )
    asyncio.run(worker.run())
