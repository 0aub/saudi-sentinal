# Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "Alert Types & Rules"
"""
Alert rule definitions for all 9 Saudi Sentinel AI projects.

Each rule specifies:
  condition: Python-evaluable expression over prediction summary stats
  severity:  "info" | "warning" | "critical"
  message:   f-string template with variables from prediction summary

Alert types in the alerts DB table:
  change_detected, drift_warning, data_gap, spill_detected,
  farm_abandoned, vegetation_loss, high_risk_expansion, etc.

See: docs/plans/LEVEL-3-SYSTEM.md — "Alert Types & Rules" code block
"""

ALERT_RULES = {
    "urban-sprawl": {
        "significant_change": {
            "condition": "change_area_km2 > 0.5",
            "severity": "info",
            "message": "New urban expansion detected: {change_area_km2:.1f} km²",
        },
        "abnormal_spike": {
            "condition": "change_area_km2 > (rolling_avg_30d * 3)",
            "severity": "warning",
            "message": "Unusual urban change spike: {ratio:.1f}× above normal",
        },
    },
    "green-riyadh": {
        "vegetation_loss": {
            "condition": "ndvi_change < -0.05",  # over 3 months
            "severity": "warning",
            "message": "Vegetation decline detected in {district}: ΔNDVI = {change:.3f}",
        },
        "greening_milestone": {
            "condition": "green_area_km2 >= milestone_threshold",
            "severity": "info",
            "message": "Green cover milestone: {green_area_km2:.1f} km²",
        },
    },
    "crop-mapping": {
        "crop_shift": {
            "condition": "dominant_crop_changed",
            "severity": "info",
            "message": "Dominant crop shift detected in {region}: {prev_crop} → {new_crop}",
        },
    },
    "groundwater": {
        "farm_abandoned": {
            "condition": "consecutive_inactive_years >= 2",
            "severity": "warning",
            "message": "{count} farms appear abandoned in {region}",
        },
        "rapid_loss": {
            "condition": "annual_pct_change < -10",
            "severity": "critical",
            "message": "Rapid farm loss: {annual_pct_change:.0f}% decline in {region} this year",
        },
    },
    "desertification": {
        "high_risk_expansion": {
            "condition": "high_risk_area_increase_pct > 10",
            "severity": "warning",
            "message": "Desertification risk expanding in {region}: +{pct:.0f}% high-risk area",
        },
        "drift_warning": {
            "condition": "psi > 0.1",
            "severity": "warning",
            "message": "Model drift detected — PSI: {psi:.3f}. Consider retraining.",
        },
    },
    "neom-tracker": {
        "construction_advance": {
            "condition": "construction_front_km > prev_front_km + 1.0",
            "severity": "info",
            "message": "NEOM construction front advanced {advance:.1f} km",
        },
    },
    "dune-migration": {
        "high_migration_speed": {
            "condition": "max_migration_speed_m_per_year > 30",
            "severity": "warning",
            "message": "High dune migration: {max_speed:.0f} m/year near {location}",
        },
    },
    "flash-flood": {
        "high_risk_area": {
            "condition": "high_risk_area_km2 > threshold",
            "severity": "info",
            "message": "Flash flood risk map updated. High-risk area: {area:.1f} km²",
        },
    },
    "oil-spill": {
        "spill_detected": {
            "condition": "confidence > 0.65 and wind_speed_ms > 3",
            "severity": "critical",
            "message": "Potential oil spill at {lat:.4f}°N {lon:.4f}°E (confidence: {conf:.0%})",
        },
        "low_confidence_detection": {
            "condition": "confidence > 0.45 and confidence <= 0.65",
            "severity": "warning",
            "message": "Low-confidence dark patch detected — manual review required",
        },
    },
}
