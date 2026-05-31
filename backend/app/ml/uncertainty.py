"""
Uncertainty estimation via Monte Carlo Dropout for LungSight AI.
Provides prediction variance, entropy-based uncertainty, and reliability classification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import torch
import torch.nn as nn


# ──────────────────────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class UncertaintyResult:
    mean_probability: float         # mean softmax prob for predicted class
    confidence_percent: float       # 0–100
    uncertainty_percent: float      # 0–100
    variance: float                 # prediction variance across MC samples
    entropy: float                  # predictive entropy (bits)
    reliability: str                # "High" | "Medium" | "Low"
    reliability_color: str
    mc_samples: int
    all_pneumonia_probs: List[float]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _enable_dropout(model: nn.Module) -> None:
    """Set Dropout layers to train mode while keeping BatchNorm in eval."""
    for m in model.modules():
        if isinstance(m, nn.Dropout):
            m.train()


def _predictive_entropy(probs: np.ndarray) -> float:
    """Shannon entropy of the mean predictive distribution (bits)."""
    p = np.clip(probs, 1e-8, 1.0)
    return float(-np.sum(p * np.log2(p)))


def _reliability(confidence: float, uncertainty: float) -> tuple[str, str]:
    if confidence >= 0.90 and uncertainty <= 0.10:
        return "High",   "#22c55e"
    if confidence >= 0.70 and uncertainty <= 0.25:
        return "Medium", "#f59e0b"
    return "Low", "#ef4444"


# ──────────────────────────────────────────────────────────────────────────────
# Estimator
# ──────────────────────────────────────────────────────────────────────────────

class MCDropoutEstimator:
    """
    Monte Carlo Dropout uncertainty estimation.
    Performs T forward passes with dropout enabled, then computes
    mean, variance, and entropy over the stochastic outputs.
    """

    def __init__(self, model: nn.Module, device: torch.device, n_samples: int = 20):
        self.model  = model
        self.device = device
        self.n_samples = n_samples

    # ------------------------------------------------------------------
    @torch.no_grad()
    def estimate(self, tensor: np.ndarray) -> UncertaintyResult:
        """
        tensor: float32 1×3×H×W numpy array.
        Returns UncertaintyResult with mean, variance, entropy, reliability.
        """
        t = torch.from_numpy(tensor).to(self.device)

        # Temporarily enable dropout during inference
        self.model.eval()
        _enable_dropout(self.model)

        pneu_probs: List[float] = []
        for _ in range(self.n_samples):
            with torch.no_grad():
                logits = self.model(t)
                probs  = torch.softmax(logits, dim=1).squeeze().cpu().numpy()
                pneu_probs.append(float(probs[1]))

        # Restore eval mode (all dropout disabled)
        self.model.eval()

        arr   = np.array(pneu_probs)
        mean  = float(arr.mean())
        var   = float(arr.var())
        label_prob = mean if mean > 0.5 else (1 - mean)
        uncertainty = float(arr.std())

        # Entropy over [normal_prob, pneumonia_prob]
        mean_dist = np.array([1 - mean, mean])
        entropy = _predictive_entropy(mean_dist)

        confidence_pct  = round(label_prob * 100, 1)
        uncertainty_pct = round(min(uncertainty * 200, 100.0), 1)
        reliability, color = _reliability(label_prob, uncertainty)

        return UncertaintyResult(
            mean_probability=round(mean, 4),
            confidence_percent=confidence_pct,
            uncertainty_percent=uncertainty_pct,
            variance=round(var, 6),
            entropy=round(entropy, 4),
            reliability=reliability,
            reliability_color=color,
            mc_samples=self.n_samples,
            all_pneumonia_probs=[round(p, 4) for p in pneu_probs],
        )
