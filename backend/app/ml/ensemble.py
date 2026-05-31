"""
Ensemble prediction module for LungSight AI.
Weighted-average voting across DenseNet121, EfficientNetB3, ResNet50.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import torch

from app.ml.models import ClassificationModelRegistry, PredictionResult


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_ENSEMBLE_MODELS = ["DenseNet121", "EfficientNetB3", "ResNet50"]

# Weights based on expected validation performance (tuned post-training)
DEFAULT_WEIGHTS = {
    "DenseNet121":    0.40,
    "EfficientNetB3": 0.35,
    "ResNet50":       0.25,
}


# ──────────────────────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class EnsemblePredictionResult:
    label: str
    confidence: float
    pneumonia_probability: float
    normal_probability: float
    individual_predictions: Dict[str, float]   # model → pneumonia_prob
    weights_used: Dict[str, float]
    total_inference_time_ms: float
    agreement_score: float   # how much models agree (0–1)


# ──────────────────────────────────────────────────────────────────────────────
# Engine
# ──────────────────────────────────────────────────────────────────────────────

class EnsemblePredictor:
    """Weighted-average ensemble over multiple classification models."""

    LABELS = ["NORMAL", "PNEUMONIA"]

    def __init__(
        self,
        registry: ClassificationModelRegistry,
        models: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.registry = registry
        self.models   = models or DEFAULT_ENSEMBLE_MODELS
        self.weights  = weights or {m: DEFAULT_WEIGHTS.get(m, 1.0) for m in self.models}
        # Normalise
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

    # ------------------------------------------------------------------
    def predict(self, tensor: np.ndarray) -> EnsemblePredictionResult:
        t_start = time.perf_counter()

        individual: Dict[str, float] = {}
        weighted_pneu = 0.0

        for model_name in self.models:
            result: PredictionResult = self.registry.predict(tensor, model_name)
            p = result.pneumonia_probability
            individual[model_name] = round(p, 4)
            weighted_pneu += self.weights[model_name] * p

        elapsed_ms = (time.perf_counter() - t_start) * 1000
        weighted_norm = 1.0 - weighted_pneu
        label = "PNEUMONIA" if weighted_pneu >= 0.5 else "NORMAL"
        confidence = weighted_pneu if label == "PNEUMONIA" else weighted_norm

        # Agreement: 1 - std of individual probs
        probs_arr = np.array(list(individual.values()))
        agreement = float(1.0 - probs_arr.std())

        return EnsemblePredictionResult(
            label=label,
            confidence=round(float(confidence), 4),
            pneumonia_probability=round(float(weighted_pneu), 4),
            normal_probability=round(float(weighted_norm), 4),
            individual_predictions=individual,
            weights_used=self.weights,
            total_inference_time_ms=round(elapsed_ms, 2),
            agreement_score=round(agreement, 4),
        )
