# Notebook 09 — Oil Spill Detection

**Status:** ⚠️ Yellow Light
**Priority:** Low
**Estimated Effort:** 6-8 days
**Difficulty:** High
**Caveat:** High false-positive rate. Calm water, biogenic films, and wind shadows mimic oil slicks in SAR.

---

## Problem Statement

Detect oil slicks in the Arabian Gulf using Sentinel-1 SAR imagery. Oil dampens surface waves, creating dark patches in SAR images that are distinguishable from clean water. Build a semantic segmentation model that classifies each water pixel as clean or potentially contaminated.

## Reality Check

- Oil on water genuinely dampens SAR backscatter → dark anomalies are visible
- **The problem is specificity**: many other things create dark patches too
  - Low-wind zones (calm water)
  - Biogenic slicks (natural surfactants from algae)
  - Rain cells
  - Ship wakes (sometimes)
  - SAR processing artifacts near coast
- Published studies report false-positive rates of 30-60% without extensive post-processing
- This project requires **aggressive false-positive filtering** to be production-useful

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensor** | Sentinel-1 GRD (IW mode) |
| **AOI** | `arabian-gulf-coast` (~300 km of Saudi Arabian Gulf coastline) |
| **Channels** | VV, VH polarization |
| **Time range** | 2019–2024 |
| **Temporal resolution** | All available scenes |
| **Supplementary** | ERA5 wind speed (free via Copernicus Climate Data Store) |
| **Chip size** | 512×512 pixels (larger for sea context) |

### Why Wind Speed Matters

| Wind Speed | Effect on SAR | Oil Detectability |
|-----------|--------------|-------------------|
| < 3 m/s | Entire sea surface is calm (dark) | **Cannot detect oil** — everything looks the same |
| 3–10 m/s | Normal sea clutter (bright) | **Optimal** — oil slicks create visible dark contrast |
| > 10 m/s | Rough sea (very bright) | Oil may be mixed into water; reduced detectability |

**Critical filter:** Discard all scenes with wind speed < 3 m/s — these are useless for oil detection.

---

## Labeling Strategy

### Using Existing Datasets + Transfer Learning

1. **Pre-training:** Use publicly available oil spill SAR datasets:
   - Marine Pollution Monitoring (EU CleanSeaNet archives, if accessible)
   - Published annotated datasets from research papers
2. **Fine-tuning:** Manually annotate ~200 chips from Arabian Gulf SAR scenes
3. **Active Learning:** Run initial model → manually verify top-confidence detections → add to training set

**Key labeling challenge:** Distinguishing oil from look-alikes requires contextual clues (proximity to shipping lanes, refineries, platforms; shape characteristics — oil tends to form elongated streaks along wind direction).

---

## Model Architecture

### Primary: DeepLabV3+ with Dark Patch Classification

```
Two-stage pipeline:

Stage 1: Dark Patch Detection
  SAR image (512×512×2) ──► DeepLabV3+ (ResNet50) ──► Binary mask: dark anomaly / normal water

Stage 2: Look-Alike Discrimination
  For each detected dark patch, extract:
    - Shape features (elongation, compactness, area)
    - Texture features (GLCM contrast, homogeneity inside/outside)
    - Contextual features (distance to coast, shipping lane, wind speed)
    - Damping ratio (backscatter inside / backscatter outside)
      │
      ▼
  Random Forest ──► {oil_spill, look-alike}
```

- **Stage 1** has high recall (catches all dark patches)
- **Stage 2** filters false positives using domain knowledge features
- This two-stage approach is standard in operational oil spill monitoring

---

## Notebook Structure

```
notebooks/09-oil-spill/
├── 01_data_exploration.ipynb       # Arabian Gulf SAR coverage, known spill locations
├── 02_sar_preprocessing.ipynb      # Calibration, land masking, speckle filtering
├── 03_wind_filtering.ipynb         # ERA5 wind speed integration, scene filtering
├── 04_dark_patch_detection.ipynb   # DeepLabV3+ training for anomaly segmentation
├── 05_feature_extraction.ipynb     # Shape, texture, context features per patch
├── 06_lookalike_classifier.ipynb   # RF classifier: oil vs. look-alike
├── 07_evaluation.ipynb             # Full pipeline evaluation, false positive analysis
└── utils/
    ├── land_mask.py                # Mask out land pixels from SAR
    ├── glcm_features.py            # Gray-Level Co-occurrence Matrix texture features
    ├── shape_features.py           # Patch geometry descriptors
    └── wind_data.py                # ERA5 wind speed retrieval
```

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **Stage 1 Recall** | > 0.90 | Catch all dark anomalies |
| **Stage 2 Precision (oil class)** | > 0.60 | At least 60% of flagged events are real (ambitious for SAR) |
| **Overall F1 (oil class)** | > 0.55 | Combined pipeline performance |
| **False Positive Rate** | < 0.40 | Less than 40% of detections are false alarms |

**Note:** These targets are realistic for Sentinel-1 SAR oil detection. Commercial systems using VHR SAR achieve better results, but at 10m free data, this is the ceiling.

---

## Known Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Wind-calms create massive false positives | Filter scenes with wind < 3 m/s; weight damping ratio feature |
| Biogenic slicks common in warm Gulf waters | Shape-based filtering (biogenic = irregular; oil = elongated streaks) |
| Limited labeled oil spill data for Arabian Gulf | Transfer learn from Mediterranean/North Sea datasets |
| Near-coast SAR artifacts | Land mask buffer of 1km; ignore near-shore detections |
| Seasonal variation in false positive rate | Separate models or threshold calibration per season |

---

## Exit Criteria

- [ ] SAR preprocessing pipeline handles land masking + wind filtering
- [ ] DeepLabV3+ detects dark anomalies with recall > 0.90
- [ ] Look-alike classifier reduces false positives to < 40%
- [ ] Pipeline tested on at least 100 SAR scenes
- [ ] Known oil spill events (if any in record) detected by pipeline
- [ ] Model exported for serving
- [ ] Notebook is reproducible

## Honest Assessment

This is the most challenging project in the portfolio. A false-positive rate of 40% means that in production, roughly 2 out of 5 alerts would be wrong. For a real production system, this would need to be combined with ship AIS tracking data, proximity to known infrastructure, and human-in-the-loop verification. The notebook demonstrates the AI capability; the MLOps layer must include human verification workflow.
