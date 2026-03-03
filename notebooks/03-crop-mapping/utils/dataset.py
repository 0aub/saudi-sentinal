# Implementation guide: see docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Model Architecture"
"""
PyTorch Dataset for temporal crop type classification.

Input to Temporal Attention Network (TANet):
  Temporal stack of 12 monthly composites × 10 bands = (12, 256, 256, 10)
  Reshaped for model as (10, 12, 256, 256) — channels, time, height, width

Target:
  Per-pixel crop class label (6 classes):
    0 = Wheat, 1 = Alfalfa, 2 = Date Palm, 3 = Fodder/Grass,
    4 = Fallow/Bare, 5 = Active Pivot (unclassified crop)

See: docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Model Architecture → TANet"
"""

from __future__ import annotations

from typing import Dict, List, Optional

import torch
from torch.utils.data import Dataset

CROP_CLASSES = {
    0: "wheat",
    1: "alfalfa",
    2: "date_palm",
    3: "fodder_grass",
    4: "fallow_bare",
    5: "active_pivot",
}


class CropMappingDataset(Dataset):
    """
    Dataset of (temporal_stack, crop_label_mask) pairs for TANet training.

    Implementation guide: docs/plans/level-1-notebooks/03-crop-type-mapping.md

    Args:
        farm_records:   List of dicts with keys: farm_id, aoi_id, crop_class, chips_by_month
        tile_api_url:   Level 0 Tile API URL for fetching monthly composite chips
        year:           Target year (single annual growing season)
        bands:          List of 10 band names to include
        transform:      Optional augmentation transform
    """

    BANDS = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
    N_CLASSES = 6
    N_MONTHS = 12

    def __init__(
        self,
        farm_records: List[Dict],
        tile_api_url: str,
        year: int = 2023,
        bands: Optional[List[str]] = None,
        transform=None,
    ) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self, idx: int):
        """
        Returns:
            temporal_stack: Tensor shape (10, 12, 256, 256) — bands × months × H × W
            label:          Tensor shape (256, 256) long — crop class per pixel
        """
        raise NotImplementedError
