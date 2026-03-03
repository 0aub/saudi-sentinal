# Notebook 07 — Sand Dune Migration Predictor

**Status:** ⚠️ Yellow Light
**Priority:** Low-Medium
**Estimated Effort:** 7-10 days
**Difficulty:** High
**Caveat:** Requires self-generated labels from multi-temporal image pairs. More research-oriented.

---

## Problem Statement

Predict sand dune migration patterns in northern Rub' al Khali using Sentinel-1 SAR time-series. Dune migration threatens roads, pipelines, and settlements — a predictive model enables proactive mitigation (sand fences, stabilization planting).

## Reality Check

- SAR can detect dune morphology (crest lines, slip faces) at 10m
- Dune migration is slow (typically 5-50 m/year) — detectable over multi-year Sentinel archive
- **The hard part:** No existing labeled dataset for Saudi dune migration. You must generate your own training data through cross-correlation of image pairs.

---

## Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Sensor** | Sentinel-1 GRD (SAR) — preferred for sand dune detection |
| **AOI** | `rub-al-khali-north` (200×200 km) |
| **Channels** | VV polarization (more sensitive to surface roughness/dune forms) |
| **Time range** | 2017–2024 (7 years for migration trend detection) |
| **Temporal resolution** | Quarterly composites (reduce speckle, enough for slow migration) |
| **Chip size** | 256×256 pixels |

---

## Label Generation (Self-Supervised)

Since no ground truth exists, generate displacement labels using image cross-correlation:

1. Take SAR image pair (T1, T2) separated by 1 year
2. For each pixel, compute **Normalized Cross-Correlation (NCC)** in a search window
3. Peak correlation location gives displacement vector (dx, dy)
4. Filter unreliable displacement vectors (low correlation = uncertain)
5. Result: dense displacement field (optical flow analog for SAR)

This is a well-established technique in dune geomorphology literature.

---

## Model Architecture

### Primary: ConvLSTM Displacement Predictor

```
Input: 7 years × quarterly = 28 SAR images per chip

Year 1–5 SAR stack (20 images) ──► [ConvLSTM Encoder] ──► Hidden State
                                                              │
                                            [ConvLSTM Decoder] ──► Predicted displacement Year 6–7
                                                                    (dx, dy per pixel)
                                                              │
                                         Compare with ──► Actual displacement Year 6–7
                                         (from NCC)           (validation target)
```

- **Input:** Temporal stack of SAR intensity images (quarterly, 5 years for training)
- **Output:** Predicted displacement vectors for next 2 years
- **Loss:** L1 loss on displacement magnitude + angular error on direction
- **Architecture:** ConvLSTM (captures spatial + temporal patterns jointly)

### Baseline

| Method | Description | Expected MAE |
|--------|-----------|-------------|
| Mean displacement (naive) | Average past displacement forward | ~15m |
| Linear extrapolation | Fit linear trend to displacement history | ~10m |
| **ConvLSTM** | **Learned spatial-temporal prediction** | **~6-8m** |

---

## Notebook Structure

```
notebooks/07-dune-migration/
├── 01_data_exploration.ipynb       # Visualize dune fields, SAR intensity patterns
├── 02_speckle_filtering.ipynb      # Lee/Gamma MAP filter on S1 imagery
├── 03_ncc_displacement.ipynb       # Cross-correlation displacement field generation
├── 04_displacement_analysis.ipynb  # Visualize migration patterns, speeds, directions
├── 05_dataset_preparation.ipynb    # Create temporal stacks + displacement labels
├── 06_convlstm_training.ipynb      # Train displacement predictor
├── 07_evaluation.ipynb             # Displacement error maps, directional accuracy
└── utils/
    ├── speckle_filter.py           # SAR speckle filtering algorithms
    ├── ncc.py                      # Normalized cross-correlation displacement
    └── convlstm.py                 # ConvLSTM implementation
```

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **Mean Absolute Error (displacement)** | < 8m | Average error in predicted migration distance |
| **Angular accuracy** | > 70% within ±15° | Direction prediction accuracy |
| **Correlation with observed** | R² > 0.6 | Predicted vs actual displacement magnitude |

---

## Exit Criteria

- [ ] NCC displacement fields generated for all available year-pairs
- [ ] ConvLSTM beats linear extrapolation baseline
- [ ] Migration speed and direction maps generated for the AOI
- [ ] Model exported for inference
- [ ] Notebook is reproducible
