# Notebook 05 — Desertification Early Warning

**Status:** ✅ Green Light
**Priority:** Medium
**Estimated Effort:** 5-7 days
**Difficulty:** Medium

---

## Problem Statement

Build an early warning system that identifies areas at risk of desertification along Saudi Arabia's agricultural margins — the transition zones between productive land and desert. Fuse Sentinel-2 optical data (vegetation health) with Sentinel-1 SAR data (soil moisture proxy) to create a multi-factor risk score.

## Why It Matters

Desertification threatens the remaining productive land in Saudi Arabia. Early detection (months to years before total degradation) enables intervention — targeted irrigation, soil stabilization, or controlled retreat. This is directly relevant to Saudi Green Initiative goals.

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensors** | Sentinel-2 L2A + Sentinel-1 GRD |
| **AOIs** | `qassim-agri-edge`, margins of `aljouf-farms`, `hail-farms` |
| **S2 Bands** | B04, B08 (NDVI), B11 (SWIR — moisture sensitivity) |
| **S1 Channels** | VV, VH polarization (soil moisture proxy: VH/VV ratio) |
| **Time range** | 2019–2024 |
| **Temporal resolution** | Monthly composites for both S1 and S2 |
| **Chip size** | 256×256 pixels |
| **Source** | Level 0 Tile API |

### Derived Features (per pixel, per month)

| Feature | Source | Formula / Description |
|---------|--------|----------------------|
| NDVI | S2 | (B08 - B04) / (B08 + B04) |
| SAVI | S2 | 1.5 × (B08-B04) / (B08 + B04 + 0.5) |
| NMDI (Normalized Moisture Diff Index) | S2 | (B08 - (B11-B12)) / (B08 + (B11-B12)) |
| Soil moisture proxy | S1 | VH/VV ratio (higher = more moisture) |
| NDVI trend (12-month) | Derived | Linear slope of last 12 NDVI values |
| NDVI variability | Derived | Std deviation of last 12 NDVI values |
| Cross-polarization ratio | S1 | VH - VV (dB) — sensitive to surface roughness |

---

## Labeling Strategy

### Expert-Defined Risk Zones

1. Identify known desertification hotspots from literature and Saudi environmental reports
2. Define 3 risk zones based on proximity to desert edge:
   - **Low risk**: Core agricultural area (stable NDVI > 0.2 for 5 years)
   - **Medium risk**: Agricultural margin (declining NDVI trend)
   - **High risk**: Actively degrading (NDVI collapsed in last 2 years)
3. Generate ~1,000 labeled pixels per class using the temporal signal as heuristic
4. Validate sample of 200 labels against Google Earth VHR imagery

---

## Model Architecture

### Primary: XGBoost Risk Classifier

For this problem, gradient boosting outperforms deep learning because:
- Tabular features (temporal statistics per pixel) not spatial patterns
- Limited labeled data
- Interpretability is critical for policy decisions (feature importance)

```
Feature vector per pixel (14 features):
  [NDVI_mean, NDVI_trend, NDVI_std, SAVI_mean, NMDI_mean, 
   soil_moisture_mean, soil_moisture_trend, cross_pol_ratio,
   NDVI_min, NDVI_max, months_below_threshold, 
   distance_to_desert_edge, elevation, slope]
      │
      ▼
  XGBoost Classifier ──► Risk Score (0.0 – 1.0) ──► {Low, Medium, High} risk
```

### Feature Engineering Details

| Feature | Window | Description |
|---------|--------|-------------|
| NDVI_mean | 24 months | Average vegetation health |
| NDVI_trend | 24 months | Sen's slope estimator (robust to outliers) |
| NDVI_std | 24 months | Instability indicator |
| NDVI_min | 24 months | Worst-case vegetation state |
| months_below_threshold | 24 months | Count of months where NDVI < 0.08 |
| soil_moisture_mean | 12 months | Average S1-derived soil moisture |
| soil_moisture_trend | 12 months | Is soil drying over time? |
| distance_to_desert_edge | Static | km to nearest bare desert zone |
| elevation, slope | DEM (Copernicus DEM 30m, free) | Topographic context |

### Baseline Comparison

| Method | Features | Expected AUC |
|--------|----------|-------------|
| NDVI trend only (threshold) | 1 feature | ~0.70 |
| Random Forest (optical only) | 8 features | ~0.78 |
| **XGBoost (optical + SAR + topo)** | **14 features** | **~0.85** |

---

## Notebook Structure

```
notebooks/05-desertification/
├── 01_data_exploration.ipynb       # Visualize agri margins, S1 + S2 coverage
├── 02_feature_engineering.ipynb    # Compute all 14 features per pixel
├── 03_labeling.ipynb               # Define risk zones, generate labeled dataset
├── 04_eda_features.ipynb           # Feature distributions, correlations, importance
├── 05_model_training.ipynb         # XGBoost + RF + LogReg comparison
├── 06_risk_map_generation.ipynb    # Full-AOI inference, risk score raster
├── 07_validation.ipynb             # Spatial validation, known degradation sites
└── utils/
    ├── sar_features.py             # S1 soil moisture proxy computation
    ├── optical_features.py         # S2 temporal statistics
    └── risk_scoring.py             # Risk score calibration
```

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **AUC-ROC** | > 0.83 | Discrimination between risk levels |
| **F1 (High Risk)** | > 0.75 | Catch degrading areas accurately |
| **Precision (High Risk)** | > 0.80 | Avoid false alarms in stable areas |
| **Spatial coherence** | Visual check | Risk zones should be contiguous, not scattered noise |
| **Feature importance** | Interpretable | Top features should be physically meaningful |

---

## Known Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| S1 and S2 have different revisit times | Resample both to monthly composites on same grid |
| Soil moisture proxy from SAR is noisy | Use 6-month rolling mean; VH/VV ratio more stable than raw backscatter |
| "Desertification" vs seasonal drought is ambiguous | Require sustained 24-month declining trend, not single-season dip |
| Labels are heuristic-based | Validate against known case studies; sensitivity analysis on thresholds |
| Copernicus DEM may have artifacts | Use 30m DEM smoothed with 3×3 median filter |

---

## Exit Criteria

- [ ] 14-feature dataset generated for all agricultural-margin AOIs
- [ ] XGBoost achieves AUC > 0.83 on held-out test set
- [ ] Risk map generated as GeoTIFF for each AOI
- [ ] Feature importance plot shows physically meaningful top features
- [ ] Model exported to ONNX or pickle for serving
- [ ] Notebook is reproducible end-to-end
