# Notebook 02 — Green Riyadh Vegetation Monitor

**Status:** ✅ Green Light
**Priority:** High
**Estimated Effort:** 4-5 days
**Difficulty:** Low-Medium

---

## Problem Statement

Track the progress of Saudi Arabia's "Green Riyadh" initiative by monitoring vegetation coverage changes across Riyadh using Sentinel-2 NDVI time-series. Build an AI model that classifies vegetation density zones and detects statistically significant greening or browning trends over time.

## Why It Matters

Green Riyadh aims to plant 7.5 million trees across 3,330+ locations as part of Vision 2030. Currently there is no independent, automated, city-wide monitoring system to verify progress. This project provides that — a satellite-based audit of greening claims.

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensor** | Sentinel-2 L2A |
| **AOI** | `riyadh-metro` (80×80 km) |
| **Bands** | B04 (Red), B08 (NIR) → NDVI; B03 (Green), B11 (SWIR) → NDWI |
| **Time range** | 2019–2024 (pre-initiative baseline through implementation) |
| **Temporal resolution** | Monthly median composites (reduce cloud/noise) |
| **Chip size** | 512×512 pixels (5.12×5.12 km) — larger chips for spatial context |
| **Source** | Level 0 Tile API |

### Derived Indices

| Index | Formula | Purpose |
|-------|---------|---------|
| NDVI | (B08 - B04) / (B08 + B04) | Vegetation health and density |
| NDWI | (B03 - B08) / (B03 + B08) | Water body detection (irrigated parks) |
| EVI | 2.5 × (B08-B04) / (B08 + 6×B04 - 7.5×B02 + 1) | Enhanced vegetation (better for arid regions) |
| SAVI | 1.5 × (B08-B04) / (B08 + B04 + 0.5) | Soil-adjusted vegetation (critical for desert cities) |

**Note:** SAVI and EVI are preferred over NDVI in arid regions because they account for soil background reflectance, which dominates in Riyadh.

---

## Labeling Strategy

### No Manual Labeling Needed

This project uses **index thresholding** for classification (not supervised learning for the initial model), making it label-free for the classification step.

| SAVI Range | Class | Description |
|-----------|-------|-------------|
| < 0.05 | Bare / Built-up | No vegetation |
| 0.05 – 0.15 | Sparse vegetation | Scattered trees, newly planted areas |
| 0.15 – 0.30 | Moderate vegetation | Parks, gardens, irrigated zones |
| > 0.30 | Dense vegetation | Established parks, agricultural plots |

The AI component (LSTM) is trained on the **time-series of these values** to detect trends and anomalies — this is self-supervised from the temporal signal.

---

## Model Architecture

### Pipeline: Two-Stage

**Stage 1 — Per-Pixel Vegetation Classification (Rule-Based)**
- Compute monthly SAVI/EVI composites
- Classify each pixel into 4 vegetation density classes
- Output: classified raster per month

**Stage 2 — Trend Detection (LSTM)**

```
Monthly SAVI values ──► [LSTM Encoder] ──► Trend Embedding ──► [Dense Head] ──► {Greening, Stable, Browning}
   (T=60 months)         128 hidden              64d                           3-class output
```

- **Input:** Per-pixel SAVI time-series (60 monthly values for 5 years)
- **Architecture:** Bidirectional LSTM with attention
- **Output:** Per-pixel trend classification (greening / stable / browning)
- **Alternative:** Mann-Kendall statistical test (non-parametric trend test) as baseline

### Baseline Comparison

| Method | Complexity | Purpose |
|--------|-----------|---------|
| Mann-Kendall trend test | None (stats) | Baseline trend detection |
| Linear regression on SAVI | Low | Quantify rate of change |
| **Bi-LSTM with attention** | **Medium** | Capture non-linear seasonal + trend patterns |

---

## Notebook Structure

```
notebooks/02-green-riyadh/
├── 01_data_exploration.ipynb       # NDVI/SAVI maps, seasonal patterns, cloud frequency
├── 02_monthly_composites.ipynb     # Build cloud-free monthly medians
├── 03_vegetation_classification.ipynb  # Threshold-based 4-class maps
├── 04_trend_analysis_baseline.ipynb    # Mann-Kendall + linear regression
├── 05_lstm_trend_model.ipynb       # Train LSTM on time-series
├── 06_spatial_analysis.ipynb       # Aggregate to neighborhoods/districts
├── 07_green_riyadh_report.ipynb    # Final maps, stats, progress assessment
└── utils/
    ├── compositing.py              # Cloud-free monthly composite builder
    ├── indices.py                  # NDVI, SAVI, EVI, NDWI computation
    └── trend.py                    # Mann-Kendall, Sen's slope estimator
```

---

## Key Outputs

1. **Monthly vegetation density maps** — 4-class rasters for Riyadh, 2019–2024
2. **Greening trend map** — pixel-level greening/browning classification
3. **District-level statistics** — % green cover change per Riyadh district
4. **Anomaly alerts** — areas with sudden vegetation loss (potential issue detection)
5. **Progress dashboard data** — JSON time-series for React frontend consumption

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **Vegetation class accuracy** | > 0.85 | Validated against known park locations (OpenStreetMap) |
| **Trend detection precision** | > 0.80 | Does the model correctly identify known greening sites? |
| **Temporal smoothness** | R² > 0.7 | SAVI time-series should be smooth after compositing |
| **Spatial coherence** | Moran's I > 0.6 | Vegetation classes should be spatially clustered, not noisy |

### Ground Truth Validation

- Compare detected green zones against OpenStreetMap park polygons for Riyadh
- Cross-reference with known Green Riyadh project site locations (from official announcements)
- Validate that SAVI > 0.1 threshold detects known irrigated areas visible in Google Earth

---

## Known Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| NDVI threshold of 0.1 is very low — noise sensitive | Use SAVI instead of NDVI; monthly composites reduce noise |
| Irrigated grass vs. natural desert shrub look similar | NDWI supplement to identify irrigated zones specifically |
| Shadows from buildings reduce apparent NDVI | Use sun-angle correction; exclude pixels with SCL shadow flag |
| Saudi cloud cover is low but dust storms reduce quality | Filter scenes with aerosol optical depth > threshold |
| Newly planted trees are tiny (< 10m) | Cannot detect individual saplings; detect greening in aggregate (park-level) |

---

## Exit Criteria

- [ ] Monthly SAVI composites cover 60 months (2019–2024) for riyadh-metro
- [ ] 4-class vegetation maps validated against OSM parks (accuracy > 0.85)
- [ ] LSTM trend model detects known greening sites with precision > 0.80
- [ ] Output JSON time-series exported and parseable by frontend
- [ ] Greening trend map exported as GeoTIFF with correct CRS
- [ ] Notebook is reproducible end-to-end
