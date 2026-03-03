# Notebook 08 — Flash Flood Risk Mapping

**Status:** ⚠️ Yellow Light
**Priority:** Medium
**Estimated Effort:** 5-7 days
**Difficulty:** Medium
**Caveat:** Post-event analysis and risk modeling only. Cannot detect floods in real-time (6-12 day revisit).

---

## Problem Statement

Build a flash flood risk model for Saudi wadis (seasonal riverbeds) using Sentinel-1 SAR historical flood extents combined with topographic features. The model predicts which areas are most likely to flood given terrain characteristics and historical flood frequency.

## Reality Check

- Sentinel-1 revisits every 6-12 days — most Saudi flash floods last hours, not days
- You will **miss most active flood events** in the SAR archive
- However, SAR detects **post-flood wet soil** (lower backscatter) for days after events
- The real value is a **static risk map** based on terrain + historical flood signatures, not real-time detection

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensor** | Sentinel-1 GRD (SAR — sees through clouds during storms) |
| **AOI** | `jeddah-wadis` (known flash flood area) |
| **Channels** | VV, VH polarization |
| **Time range** | 2017–2024 |
| **Temporal resolution** | All available scenes (capture as many post-flood images as possible) |
| **Supplementary** | Copernicus DEM 30m (slope, flow accumulation, TWI) |
| **Chip size** | 256×256 pixels |

### Topographic Features (from DEM)

| Feature | Description | Relevance |
|---------|-------------|-----------|
| Elevation | Height above sea level | Low areas accumulate water |
| Slope | Terrain steepness | Steep slopes = fast runoff |
| TWI (Topographic Wetness Index) | ln(catchment_area / tan(slope)) | Primary flood susceptibility indicator |
| Flow accumulation | Upstream contributing area | Wadi channels have high values |
| Aspect | Slope direction | Affects runoff patterns |
| Curvature | Surface concavity/convexity | Concave = water collection |
| Distance to nearest wadi channel | Proximity to drainage | Closer = higher risk |
| HAND (Height Above Nearest Drainage) | Elevation relative to nearest stream | Best single predictor of flood extent |

---

## Approach

### Two Components

**Component A: Historical Flood Extent Extraction**
1. Build a SAR reference baseline (mean + std of VV backscatter per pixel)
2. For each new SAR scene, flag pixels where VV < (mean - 2×std) as "potentially flooded"
3. Cross-reference with rainfall records to confirm flood events
4. Build a **flood frequency map** (how many times each pixel was flagged over 7 years)

**Component B: Risk Model**
1. Combine flood frequency map with topographic features
2. Train a classifier: pixel-level flood risk scoring
3. Output: static risk map (updated annually with new flood observations)

---

## Model Architecture

### Primary: XGBoost Flood Risk Classifier

```
Feature vector per pixel:
  [elevation, slope, TWI, flow_accum, aspect, curvature, 
   distance_to_wadi, HAND, flood_frequency, mean_backscatter,
   backscatter_variability, land_cover_class]
      │
      ▼
  XGBoost ──► Flood Risk Probability (0.0–1.0)
```

- **Why XGBoost not CNN:** Topographic features are tabular; spatial context comes from DEM-derived features (HAND, flow accumulation)
- **Training:** Pixels with flood_frequency > 2 are positive class; never-flooded pixels are negative
- **Validation:** Compare predicted high-risk zones against known Jeddah flood event extents (2009, 2011 documented)

---

## Notebook Structure

```
notebooks/08-flash-flood/
├── 01_data_exploration.ipynb       # Jeddah wadi system, SAR coverage, known flood dates
├── 02_dem_features.ipynb           # Compute all topographic features from Copernicus DEM
├── 03_sar_baseline.ipynb           # Build SAR temporal statistics (mean, std per pixel)
├── 04_flood_detection.ipynb        # Threshold-based flood extent extraction from SAR
├── 05_flood_frequency_map.ipynb    # Aggregate detected floods into frequency map
├── 06_risk_model_training.ipynb    # XGBoost on topo + SAR + flood frequency
├── 07_risk_map_generation.ipynb    # Full AOI risk map, evacuation zone delineation
└── utils/
    ├── dem_processing.py           # TWI, HAND, flow accumulation computation
    ├── sar_flood_detect.py         # SAR change detection for flood extent
    └── risk_scoring.py             # Risk probability calibration
```

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **AUC-ROC** | > 0.82 | Flood risk discrimination |
| **High-risk precision** | > 0.75 | Predicted high-risk areas are truly flood-prone |
| **Known event capture** | > 80% | Documented Jeddah floods fall within predicted high-risk zones |
| **HAND correlation** | Significant | Model should weight HAND as top feature |

---

## Exit Criteria

- [ ] Flood frequency map generated from 7 years of SAR data
- [ ] DEM-derived topographic features computed for Jeddah AOI
- [ ] XGBoost risk model achieves AUC > 0.82
- [ ] Risk map validates against documented Jeddah flood zones
- [ ] Model exported for serving
- [ ] Notebook is reproducible
