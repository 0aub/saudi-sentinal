# Implementation guide: see docs/plans/level-1-notebooks/06-neom-construction-tracker.md — "Model Architecture"
"""
Multi-sensor bi-temporal PyTorch Dataset for NEOM construction phase classification.

Inputs to Bi-temporal Fusion CNN:
  S2 T1 (2020 baseline):  Tensor shape (6, 256, 256) — 6 S2 bands
  S2 T2 (2023/2024):      Tensor shape (6, 256, 256) — 6 S2 bands
  S1 T1 (2020 baseline):  Tensor shape (2, 256, 256) — VV, VH
  S1 T2 (2023/2024):      Tensor shape (2, 256, 256) — VV, VH

Target: Per-pixel 4-class construction phase label:
  0 = Undisturbed desert
  1 = Cleared/Graded
  2 = Active construction
  3 = Completed infrastructure

See: docs/plans/level-1-notebooks/06-neom-construction-tracker.md — "Model Architecture"
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset

CONSTRUCTION_PHASES = {
    0: "undisturbed_desert",
    1: "cleared_graded",
    2: "active_construction",
    3: "completed_infrastructure",
}


class NEOMFusionDataset(Dataset):
    """
    Bi-temporal, bi-sensor dataset for NEOM construction phase classification.

    Implementation guide: docs/plans/level-1-notebooks/06-neom-construction-tracker.md
    """

    def __init__(
        self,
        chip_records: List[Dict],
        tile_api_url: str,
        baseline_year: int = 2020,
        target_year: int = 2024,
        transform=None,
    ) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, ...]:
        """
        Returns:
            (s2_t1, s2_t2, s1_t1, s1_t2, label)
            All tensors float32 except label (long).
        """
        raise NotImplementedError
