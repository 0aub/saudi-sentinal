# Implementation guide: see docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — "Notebook Structure"
"""
PyTorch Dataset for bi-temporal chip pairs (urban change detection).

Loads pairs of (T1, T2) chips from the Level 0 Tile API and returns:
  - image_t1: torch.Tensor shape (6, 256, 256) — Sentinel-2 bands at time T1
  - image_t2: torch.Tensor shape (6, 256, 256) — Sentinel-2 bands at time T2
  - label:    torch.Tensor shape (1, 256, 256) — binary change mask (0=unchanged, 1=changed)

Data split strategy: spatial (by geographic region), NOT random.
Random splitting causes data leakage because adjacent chips overlap.

See: docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — "Training Configuration"
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset


class UrbanChangeDataset(Dataset):
    """
    Dataset of (T1_chip, T2_chip, change_mask) triples for Siamese U-Net training.

    Implementation guide: docs/plans/level-1-notebooks/01-urban-sprawl-detector.md

    Args:
        chip_pairs:  List of dicts with keys: chip_id_t1, chip_id_t2, label_path
        tile_api_url: URL of Level 0 Tile API for fetching chip data
        transform:   Optional augmentation transform (see transforms.py)
        aois:        List of AOI IDs to include (e.g. ["riyadh-metro", "jeddah-metro"])
    """

    def __init__(
        self,
        chip_pairs: List[Dict],
        tile_api_url: str,
        transform=None,
        aois: Optional[List[str]] = None,
    ) -> None:
        raise NotImplementedError(
            "Implement dataset loading. "
            "See docs/plans/level-1-notebooks/01-urban-sprawl-detector.md."
        )

    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
            (image_t1, image_t2, label) — all torch.Tensor float32

        Implementation notes:
        - Fetch chips via Tile API or load from local cache
        - Normalize: divide by per-band statistics from training set
        - Apply transform (if provided) consistently to both images AND label
        - Return NaN-free tensors (replace NaN with 0.0 after normalization)
        """
        raise NotImplementedError
