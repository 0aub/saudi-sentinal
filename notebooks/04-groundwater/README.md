# Notebook 04 — Groundwater Depletion Tracker

**Status:** ✅ Green Light
**Priority:** High
**Estimated Effort:** 3-4 days
**Difficulty:** Low

---

## Problem Statement

Track the disappearance and shrinkage of circular irrigation farms across Saudi Arabia as a proxy for groundwater depletion. As aquifers are exhausted, pivot farms are abandoned — visible as green circles turning to bare desert. Quantify this trend over 5 years using Sentinel-2 binary change detection.

## Why It Matters

Saudi Arabia's non-renewable fossil aquifers are depleting rapidly. The kingdom has already lost over 50% of its wheat production capacity since the 2008 decision to phase out domestic wheat subsidies. This project provides an independent, objective measure of agricultural water stress across the country.

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensor** | Sentinel-2 L2A |
| **AOIs** | `aljouf-farms`, `hail-farms`, `tabuk-farms`, `qassim-agri-edge` |
| **Bands** | B04 (Red), B08 (NIR) → NDVI |
| **Time range** | 2019–2024, annual peak-vegetation composites |
| **Temporal resolution** | One composite per year (peak growing season: Feb–Apr) |
| **Chip size** | 512×512 pixels |
| **Source** | Level 0 Tile API |

---

## Approach

This is the simplest project in the portfolio — intentionally. It demonstrates that not every AI system needs a deep neural network.

### Pipeline

```
Annual NDVI composite ──► Threshold (NDVI > 0.15 = active farm) 
    ──► Binary mask per year ──► Diff between years 
    ──► Classify: {appeared, disappeared, persisted, never_farmed}
    ──► Aggregate statistics per region
```

### Classification Logic

| Year N | Year N+1 | Classification |
|--------|----------|---------------|
| Active (NDVI > 0.15) | Active | Persisted |
| Active | Inactive (NDVI ≤ 0.15) | **Disappeared** (abandoned) |
| Inactive | Active | **Appeared** (new farm) |
| Inactive | Inactive | Never farmed / still fallow |

### AI Enhancement: Anomaly Detection

For a more sophisticated approach, train a simple autoencoder on "healthy farm" NDVI time-series. Farms that deviate from normal patterns are flagged as at-risk.

```
5-year NDVI series (60 monthly values) ──► [Encoder] ──► Latent (8d) ──► [Decoder] ──► Reconstruction
                                                                              │
                                                          High reconstruction error = anomalous farm
```

---

## Model Architecture

### Primary: Threshold-Based Change Detection + Anomaly Autoencoder

| Component | Method | Purpose |
|-----------|--------|---------|
| Farm detection | NDVI threshold > 0.15 on annual max | Binary: farm / not-farm |
| Change detection | Year-over-year diff of binary masks | Classify transitions |
| Anomaly detection | LSTM Autoencoder on NDVI time-series | Early warning of declining farms |
| Trend quantification | Linear regression on farm pixel count | Rate of loss per region |

### Baseline

| Method | Complexity | What it gives you |
|--------|-----------|------------------|
| **NDVI thresholding + diff** | Very Low | Binary change maps per year |
| **LSTM Autoencoder** | Low-Medium | Early warning on at-risk farms |

---

## Notebook Structure

```
notebooks/04-groundwater/
├── 01_data_exploration.ipynb       # Visualize farm regions, count visible pivots
├── 02_annual_composites.ipynb      # Peak-season NDVI composites per year
├── 03_farm_detection.ipynb         # Threshold + morphological cleaning
├── 04_change_detection.ipynb       # Year-over-year farm appearance/disappearance
├── 05_trend_analysis.ipynb         # Per-region statistics, rate of loss
├── 06_anomaly_autoencoder.ipynb    # Train LSTM-AE for early warning
├── 07_regional_report.ipynb        # Maps, charts, policy-relevant statistics
└── utils/
    ├── compositing.py              # Annual peak-season composite builder
    └── farm_stats.py               # Farm counting, area calculation
```

---

## Key Outputs

1. **Annual farm count maps** — binary raster showing active farms per year
2. **Change map** — appeared / disappeared / persisted classification
3. **Regional depletion statistics** — JSON: `{region, year, active_farms, total_area_ha, pct_change}`
4. **At-risk farm alerts** — list of farms with declining NDVI trends
5. **Depletion rate dashboard data** — time-series for React frontend

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **Farm detection accuracy** | > 0.90 | Validated against manual counting in 10 sample areas |
| **Change detection precision** | > 0.85 | Confirmed abandoned farms are truly abandoned |
| **Trend direction accuracy** | > 0.90 | Regions known to be declining are flagged correctly |
| **Autoencoder anomaly precision** | > 0.70 | Flagged farms show subsequent decline within 2 years |

---

## Known Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Fallow rotation ≠ abandonment | Require 2+ consecutive years of inactivity to classify as abandoned |
| Desert greening after rain looks like farming | Use circular geometry check (pivot farms are round) to filter |
| Small farms (< 200m diameter) hard to detect at 10m | Set minimum object size filter; focus on standard pivot farms |
| Interannual NDVI variability | Use peak-season composite and 3-year rolling average |

---

## Exit Criteria

- [ ] Annual farm masks generated for 2019–2024 across all 4 AOIs
- [ ] Change map validates against visual inspection (precision > 0.85)
- [ ] Regional statistics exported as JSON
- [ ] LSTM Autoencoder trained and identifies declining farms
- [ ] Total Saudi pivot farm count and area computed per year
- [ ] Notebook is reproducible end-to-end
