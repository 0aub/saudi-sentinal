# Implementation guide: see docs/plans/level-1-notebooks/07-sand-dune-migration.md — "Model Architecture"
"""
ConvLSTM implementation for spatial-temporal dune migration prediction.

ConvLSTM extends LSTM to 2D spatial domains by replacing matrix multiplications
with convolutions. This allows the model to learn both spatial dune patterns
and temporal migration dynamics simultaneously.

Architecture:
  Input:   28 quarterly SAR images × 1 channel = (B, T, 1, H, W)
  Encoder: ConvLSTM processes first 20 timesteps → hidden state
  Decoder: ConvLSTM decodes hidden state → predicted displacement for next 8 timesteps
  Output:  Predicted (dx, dy) displacement per pixel = (B, 8, 2, H, W)

Target metric: Displacement MAE < 8m

See: docs/plans/level-1-notebooks/07-sand-dune-migration.md — "Model Architecture → ConvLSTM"
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn


class ConvLSTMCell(nn.Module):
    """
    Single ConvLSTM cell.

    Replaces the linear transformations in standard LSTM with convolutions,
    allowing spatial feature maps to be treated as the hidden state.
    """

    def __init__(
        self,
        input_channels: int,
        hidden_channels: int,
        kernel_size: int = 3,
    ) -> None:
        """
        Args:
            input_channels:  Number of input feature channels
            hidden_channels: Number of hidden state channels
            kernel_size:     Convolution kernel size (3 or 5 recommended)
        """
        super().__init__()
        raise NotImplementedError(
            "Implement ConvLSTM cell with 4 gates (input, forget, cell, output). "
            "Each gate uses a Conv2d applied to concatenated [input, hidden_state]. "
            "See docs/plans/level-1-notebooks/07-sand-dune-migration.md."
        )

    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]],
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x:      Input tensor shape (B, C_in, H, W)
            hidden: Tuple (h, c) each shape (B, C_hidden, H, W), or None

        Returns:
            (h_next, c_next) each shape (B, C_hidden, H, W)
        """
        raise NotImplementedError


class DuneMigrationPredictor(nn.Module):
    """
    Encoder-Decoder ConvLSTM for dune displacement prediction.

    Implementation guide: docs/plans/level-1-notebooks/07-sand-dune-migration.md
    """

    def __init__(
        self,
        input_channels: int = 1,
        hidden_channels: int = 64,
        n_encoder_layers: int = 2,
        n_decoder_layers: int = 2,
    ) -> None:
        super().__init__()
        raise NotImplementedError

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input SAR stack, shape (B, T_in, 1, H, W)

        Returns:
            Predicted displacement, shape (B, T_out, 2, H, W)
            where 2 channels = (dx, dy) in pixels
        """
        raise NotImplementedError
