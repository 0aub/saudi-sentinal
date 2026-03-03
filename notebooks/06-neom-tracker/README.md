# Notebook 06 — NEOM Construction Tracker

**Status:** ⚠️ Yellow Light
**Priority:** Medium
**Estimated Effort:** 5-6 days
**Difficulty:** Medium
**Caveat:** Limited to coarse-grained tracking at 10m resolution. Cannot detect building-level detail.

---

## Problem Statement

Monitor the construction progress of Saudi Arabia's NEOM megaproject (specifically The Line) using Sentinel-1 SAR and Sentinel-2 optical imagery. Classify the construction corridor into phases: undisturbed, cleared, under construction, and completed infrastructure.

## Reality Check

At 10m per pixel, you can detect:
- ✅ Land clearing and earthworks (large-scale disturbed soil)
- ✅ New road networks and access corridors
- ✅ Construction staging areas and worker camps
- ✅ Overall construction front advancement
- ❌ Individual building footprints
- ❌ Construction phase of specific structures
- ❌ Equipment or vehicle detection

This project tracks **macro-scale construction progress**, not building-level monitoring.

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensors** | Sentinel-2 L2A + Sentinel-1 GRD |
| **AOI** | `neom-line` (170×20 km strip along planned route) |
| **S2 Bands** | B02, B03, B04, B08, B11, B12 |
| **S1 Channels** | VV, VH |
| **Time range** | 2020–2024 (pre-construction baseline through active construction) |
| **Temporal resolution** | Monthly composites |
| **Chip size** | 256×256 pixels |
| **Source** | Level 0 Tile API |

---

## Labeling Strategy

### Visual Interpretation + Temporal Change

1. Use 2020 imagery as baseline (pre-construction)
2. Compare with 2023-2024 imagery to identify disturbed zones
3. Classify into 4 categories based on spectral and backscatter change:
   - **Undisturbed desert**: No change in NDVI or SAR backscatter
   - **Cleared/Graded**: Soil disturbance visible (lower NDVI, different SAR texture)
   - **Active construction**: High SAR backscatter (metal/concrete), roads visible
   - **Completed infrastructure**: Stable high backscatter, regular geometry
4. Label ~300 chips manually using visual comparison

---

## Model Architecture

### Bi-temporal Fusion Network

```
S2 T1 (2020) ─┐                    ┌─► Change Features ─┐
S2 T2 (2024) ─┤──► S2 Encoder ────►│                     │
               │   (ResNet18)       └─► S2 Diff Features  │──► Fusion ──► Classifier ──► 4 classes
S1 T1 (2020) ─┤                    ┌─► SAR Change         │     Layer
S1 T2 (2024) ─┘──► S1 Encoder ────►│                     │
                   (ResNet18)       └─► SAR Diff Features ─┘
```

- **Dual-sensor input**: Optical (S2) + SAR (S1) provide complementary information
- **SAR advantage**: Detects metal structures and construction materials independent of illumination
- **Output**: Per-pixel 4-class classification

### Baseline Comparison

| Method | Input | Expected OA |
|--------|-------|------------|
| NDVI differencing threshold | S2 only | ~0.55 |
| Random Forest on S1+S2 features | 12 features | ~0.65 |
| **Bi-temporal Fusion CNN** | **S1 + S2 pairs** | **~0.72** |

---

## Notebook Structure

```
notebooks/06-neom-tracker/
├── 01_data_exploration.ipynb       # NEOM corridor visualization, S1+S2 coverage
├── 02_baseline_comparison.ipynb    # 2020 vs 2024 visual side-by-side
├── 03_change_features.ipynb        # Compute optical + SAR change features
├── 04_labeling.ipynb               # Manual labeling of construction phases
├── 05_fusion_model_training.ipynb  # Train bi-temporal fusion CNN
├── 06_evaluation.ipynb             # Accuracy, confusion matrix, visual maps
├── 07_progress_timeline.ipynb      # Monthly construction front progression
└── utils/
    ├── sar_processing.py           # S1 speckle filtering, calibration
    └── fusion_dataset.py           # Multi-sensor PyTorch Dataset
```

---

## Key Outputs

1. **Construction phase map** — 4-class raster along The Line corridor
2. **Monthly progress animation** — GIF showing construction front advancement
3. **Construction area statistics** — km² cleared/constructed per month
4. **Progress percentage** — % of 170km corridor showing activity

---

## Evaluation & Exit Criteria

| Metric | Target |
|--------|--------|
| Overall Accuracy | > 0.70 |
| "Cleared" class IoU | > 0.65 |
| Visual plausibility | Construction maps align with known project areas |

- [ ] 4-class map generated for full NEOM corridor
- [ ] Monthly time-series of construction area computed
- [ ] S1+S2 fusion demonstrably outperforms S2-only baseline
- [ ] Model exported to ONNX
- [ ] Notebook is reproducible
