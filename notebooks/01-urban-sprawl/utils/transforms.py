# Implementation guide: see docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — "Training Configuration → augmentations"
"""
Data augmentation transforms for urban change detection.

Augmentations are applied consistently to BOTH T1 and T2 images AND the label mask.
Random state must be shared so spatial transforms align.

Training augmentations (from plan doc):
  horizontal_flip:           p=0.5
  vertical_flip:             p=0.5
  random_rotate_90:          p=0.5
  random_brightness_contrast: p=0.3  (applied independently to T1 and T2)
  elastic_transform:         p=0.2

See: docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — "Training Configuration"
"""

from __future__ import annotations

import torch


class SiamesePairTransform:
    """
    Albumentations-based transform wrapper for (T1, T2, mask) triples.

    Implementation guide: docs/plans/level-1-notebooks/01-urban-sprawl-detector.md

    Uses albumentations with additional_targets={'image_t2': 'image', 'mask': 'mask'}
    to apply identical spatial transforms to both images and the label.

    Note: brightness/contrast is applied independently to T1 and T2
    to simulate different acquisition conditions.
    """

    def __init__(self, mode: str = "train") -> None:
        """
        Args:
            mode: "train" (with augmentations) or "val"/"test" (no augmentations)
        """
        raise NotImplementedError(
            "Build albumentations Compose pipeline. "
            "See docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — augmentations."
        )

    def __call__(
        self,
        image_t1: torch.Tensor,
        image_t2: torch.Tensor,
        mask: torch.Tensor,
    ):
        """Apply transforms and return (image_t1, image_t2, mask)."""
        raise NotImplementedError
