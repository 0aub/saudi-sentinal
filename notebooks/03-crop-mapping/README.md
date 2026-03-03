# Notebook 03 — Crop Type Mapping

**Status:** ✅ Green Light
**Priority:** High
**Estimated Effort:** 6-8 days
**Difficulty:** Medium-High

---

## Problem Statement

Classify crop types in Saudi Arabia's major agricultural regions (Al-Jouf, Tabuk, Hail) using temporal stacks of Sentinel-2 imagery. Saudi circular pivot irrigation farms are clearly visible at 10m resolution, and different crops have distinct spectral-temporal signatures (phenological curves) that enable classification.

## Why It Matters

Saudi Arabia imports ~80% of its food. Understanding what is planted, where, and when directly supports food security monitoring, water allocation policy (each crop has different water demand), and agricultural subsidy planning under Vision 2030.

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensor** | Sentinel-2 L2A |
| **AOIs** | `aljouf-farms`, `tabuk-farms`, `hail-farms` |
| **Bands** | B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12 (10 bands) |
| **Time range** | Full annual cycle (Jan–Dec) per year, 2021–2024 |
| **Temporal resolution** | Every available cloud-free scene (~every 5 days) |
| **Chip size** | 512×512 pixels (5.12 km — fits multiple pivot farms) |
| **Source** | Level 0 Tile API |

### Target Crop Classes

| Class | Typical Season | Key Spectral Feature |
|-------|---------------|---------------------|
| Wheat | Nov–Apr (winter) | High NDVI peak in Feb-Mar |
| Alfalfa | Year-round (multiple cuts) | Periodic NDVI oscillations |
| Date Palm | Year-round (evergreen) | Stable moderate NDVI |
| Fodder/Grass | Variable | Lower NDVI than wheat |
| Fallow / Bare | — | NDVI < 0.1 consistently |
| Active Pivot (unclassified crop) | Variable | Any vegetation within circular geometry |

---

## Labeling Strategy

### Semi-Automated Pivot Farm Extraction

1. **Circle Detection:** Use Hough Transform on NDVI annual max to detect circular pivot farms (distinctive round shapes, typically 500m-1km diameter)
2. **Temporal profiling:** Extract NDVI time-series per detected farm
3. **Manual labeling:** Label ~500 farms using visual interpretation of temporal profiles + Google Earth VHR context
4. **Propagation:** Use labeled profiles as templates to classify remaining farms via DTW (Dynamic Time Warping) similarity

**Estimated labeling time:** 10-15 hours for 500 farms

### Alternative: Use USDA CropScape methodology
Adapt the temporal CNN approach used for US cropland but retrain entirely on Saudi phenology.

---

## Model Architecture

### Primary: Temporal Attention Network (TANet)

```
Per-pixel temporal stack           Temporal         Spatial          Classification
  (T×H×W×B)                       Encoder          Encoder          Head
                                                    
12 dates × 256×256 × 10 bands ──► [1D Conv + LSTM] ──► [2D Conv] ──► Softmax (6 classes)
                                   per-pixel            spatial        per-pixel
                                   temporal features    context        crop type
```

- **Input:** Stack of 12 monthly composites × 10 bands = (12, 256, 256, 10)
- **Temporal encoder:** 1D convolutions along time axis + LSTM to capture phenology
- **Spatial encoder:** 2D convolutions for spatial context (field boundaries)
- **Output:** Per-pixel classification into 6 crop classes
- **Loss:** Weighted Cross-Entropy (balance rare crops like date palms)
- **Framework:** PyTorch

### Baseline Comparison

| Method | Input | Expected OA |
|--------|-------|------------|
| Max-NDVI threshold | Single date | ~0.50 |
| Random Forest on temporal features | Handcrafted phenology features | ~0.70 |
| 3D CNN (spatial + temporal) | Monthly stack | ~0.75 |
| **Temporal Attention Network** | **Monthly stack** | **~0.80** |

---

## Notebook Structure

```
notebooks/03-crop-mapping/
├── 01_data_exploration.ipynb       # Visualize farms, NDVI profiles, seasonal patterns
├── 02_pivot_detection.ipynb        # Hough Transform circle detection on NDVI max
├── 03_temporal_profiles.ipynb      # Extract and cluster NDVI time-series per farm
├── 04_labeling_and_dataset.ipynb   # Label farms, create train/val/test split
├── 05_baseline_rf.ipynb            # Random Forest on phenology features
├── 06_temporal_cnn_training.ipynb  # Train Temporal Attention Network
├── 07_evaluation.ipynb             # Per-class accuracy, confusion matrix, maps
├── 08_full_region_inference.ipynb  # Run on full AOIs, export crop type maps
└── utils/
    ├── pivot_detection.py          # Circle detection algorithms
    ├── temporal_features.py        # Phenology feature extraction (peak date, amplitude, etc.)
    ├── dtw.py                      # Dynamic Time Warping for profile matching
    └── dataset.py                  # PyTorch Dataset for temporal stacks
```

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **Overall Accuracy (OA)** | > 0.78 | Across all classes |
| **Per-class F1** | > 0.70 each | Each crop type individually |
| **Wheat F1** | > 0.85 | Most important crop for food security |
| **Kappa coefficient** | > 0.70 | Agreement beyond chance |
| **Farm-level accuracy** | > 0.85 | Majority-vote classification per detected farm |

---

## Known Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Multiple crops per year on same pivot | Use full annual temporal stack; LSTM captures multiple peaks |
| Alfalfa has 5-7 cuts/year — complex signal | DTW-based matching handles irregular patterns better than LSTM |
| Some pivots are partially irrigated (half circles) | Include partial pivots in training; don't rely on geometry alone |
| Cloud gaps in temporal stack | Interpolate missing dates with linear interpolation; monthly composites help |
| Limited labeled data | Data augmentation: temporal shift ±5 days, add Gaussian noise to NDVI |

---

## Exit Criteria

- [ ] Pivot farm detection finds > 90% of visible farms in test AOI
- [ ] Temporal Attention Network achieves OA > 0.78 on held-out test farms
- [ ] Wheat class specifically achieves F1 > 0.85
- [ ] Crop type map exported as GeoTIFF for each AOI region
- [ ] Model exported to ONNX format
- [ ] Inference on one full AOI completes in < 60 minutes on GPU
- [ ] Notebook is reproducible end-to-end
