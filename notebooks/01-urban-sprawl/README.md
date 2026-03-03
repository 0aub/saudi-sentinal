# Notebook 01 — Urban Sprawl Detector

**Status:** ✅ Green Light
**Priority:** High
**Estimated Effort:** 5-7 days
**Difficulty:** Medium

---

## Problem Statement

Detect and quantify new urban construction and expansion across Saudi Arabia's major cities (Riyadh, Jeddah, Dammam) using Sentinel-2 multi-temporal imagery. The model should classify each pixel as *changed (new construction)* or *unchanged* between two time periods.

## Why It Matters

Saudi Vision 2030 is driving massive urban transformation. Riyadh alone is expanding rapidly with projects like the Sports Boulevard (135km), Diriyah Gate, and King Salman Park. Automated change detection provides urban planners with objective, frequent expansion monitoring without relying on manual surveys.

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensor** | Sentinel-2 L2A |
| **AOIs** | `riyadh-metro`, `jeddah-metro`, `dammam-metro` |
| **Bands** | B02, B03, B04, B08 (10m); B11, B12 (20m resampled to 10m) |
| **Time range** | 2019–2024 (5 years of change) |
| **Pair strategy** | Compare yearly composites (e.g., 2022 vs. 2024) |
| **Chip size** | 256×256 pixels (2.56×2.56 km) |
| **Min samples** | ~2,000 chip pairs per city (after cloud filtering) |
| **Source** | Level 0 Tile API |

### Derived Features

| Feature | Formula | Purpose |
|---------|---------|---------|
| NDBI (Built-up Index) | (B11 - B08) / (B11 + B08) | Highlights built-up areas |
| NDVI (Vegetation Index) | (B08 - B04) / (B08 + B04) | Distinguishes green from urban |
| BSI (Bare Soil Index) | ((B11+B04)-(B08+B02)) / ((B11+B04)+(B08+B02)) | Separates soil from construction |
| Difference stack | T2 - T1 for each index | Change magnitude per index |

---

## Labeling Strategy

### Option A — Semi-Automated (Recommended)

1. Compute NDBI difference between T1 and T2 yearly composites
2. Threshold at ΔNDBI > 0.15 to generate **noisy pseudo-labels**
3. Manually correct ~500 chips using QGIS (clean labels)
4. Train on noisy labels → fine-tune on clean labels (noise-robust training)

### Option B — Transfer Learning

1. Use pretrained urban change detection model from SpaceNet or xView2
2. Fine-tune on ~200 manually labeled Saudi chips
3. Lower labeling effort but may underperform on desert-to-urban transitions

**Estimated labeling time:** 15-20 hours for 500 clean chips

---

## Model Architecture

### Primary: Siamese U-Net

```
Input T1 (256×256×6) ──► Encoder (ResNet34) ──► Feature Map T1
                                                        │
                                                   Concatenate ──► Decoder ──► Change Map (256×256×1)
                                                        │
Input T2 (256×256×6) ──► Encoder (ResNet34) ──► Feature Map T2
                         (shared weights)
```

- **Backbone:** ResNet34 pretrained on ImageNet (transfer to satellite via fine-tuning)
- **Decoder:** U-Net decoder with skip connections
- **Output:** Binary segmentation mask (changed / unchanged)
- **Loss:** Binary Cross-Entropy + Dice Loss (handles class imbalance — most pixels are unchanged)
- **Framework:** PyTorch + segmentation_models_pytorch

### Baseline Comparison

| Model | Complexity | Expected IoU |
|-------|-----------|-------------|
| Thresholded NDBI diff | None (rule-based) | ~0.45 |
| Random Forest on pixel features | Low | ~0.55 |
| U-Net (single-date) | Medium | ~0.60 |
| **Siamese U-Net (bi-temporal)** | **Medium-High** | **~0.70** |

---

## Notebook Structure

```
notebooks/01-urban-sprawl/
├── 01_data_exploration.ipynb       # Visualize AOIs, cloud stats, temporal coverage
├── 02_feature_engineering.ipynb    # Compute indices (NDBI, NDVI, BSI), create pairs
├── 03_labeling_pipeline.ipynb      # Generate pseudo-labels + manual correction guide
├── 04_baseline_models.ipynb        # Thresholding, Random Forest benchmarks
├── 05_siamese_unet_training.ipynb  # Full model training + hyperparameter tuning
├── 06_evaluation.ipynb             # Metrics, confusion matrix, visual results
├── 07_inference_demo.ipynb         # Run on new unseen dates, export GeoTIFF predictions
└── utils/
    ├── dataset.py                  # PyTorch Dataset for chip pairs
    ├── transforms.py               # Augmentations (flip, rotate, elastic)
    └── metrics.py                  # IoU, F1, precision, recall for change detection
```

---

## Training Configuration

```yaml
training:
  epochs: 50
  batch_size: 16
  learning_rate: 1e-4
  scheduler: CosineAnnealingLR
  optimizer: AdamW
  weight_decay: 1e-4
  early_stopping_patience: 10
  
augmentations:
  horizontal_flip: 0.5
  vertical_flip: 0.5
  random_rotate_90: 0.5
  random_brightness_contrast: 0.3
  elastic_transform: 0.2

data_split:
  train: 0.7
  val: 0.15
  test: 0.15
  split_by: spatial  # Split by geographic region, NOT random chips
```

**Important:** Split by spatial region, not randomly. Random splitting causes data leakage since adjacent chips overlap.

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **IoU (change class)** | > 0.65 | Primary metric — intersection over union for "changed" pixels |
| **F1-score** | > 0.70 | Harmonic mean of precision and recall |
| **Precision** | > 0.75 | Avoid false positives (flagging sand as construction) |
| **Recall** | > 0.65 | Catch most real construction events |
| **FAR (False Alarm Rate)** | < 0.15 | Critical for production: too many false alarms = useless system |

### Visual Validation Checklist

- [ ] Model correctly identifies new residential blocks in Riyadh suburbs
- [ ] Model does NOT flag seasonal vegetation change as construction
- [ ] Model does NOT flag cloud shadows as change
- [ ] Model handles desert-to-construction transitions (not just urban infill)
- [ ] Change maps align with known Saudi mega-project locations

---

## Known Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Sand and bare soil look like construction at 10m | Include BSI as input feature; use temporal stability (construction persists, sand doesn't) |
| Class imbalance (90%+ unchanged) | Dice loss + focal loss; oversample change chips |
| Cloud contamination | Use SCL mask from Level 0; create annual median composites |
| Seasonal brightness variation | Use surface reflectance (L2A), not TOA; normalize per-scene |
| Different cities have different construction patterns | Train on all 3 cities jointly; evaluate per-city |

---

## Exit Criteria (Must Pass Before Level 2)

- [ ] Siamese U-Net achieves IoU > 0.65 on held-out test set
- [ ] Visual inspection on 50 random test chips shows < 10% obvious errors
- [ ] Model runs inference on a full AOI (riyadh-metro) in < 30 minutes on GPU
- [ ] Model exported to ONNX format successfully
- [ ] Inference GeoTIFF output has correct CRS and georeference metadata
- [ ] Notebook is reproducible: clear cells → Run All → same results
