"""
Classification model registry for LungSight AI.
Implements DenseNet121, EfficientNetB3, ResNet50, VGG16
with ImageNet transfer-learning and fine-tuned heads.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tv_models
from torchvision.models import (
    DenseNet121_Weights,
    EfficientNet_B3_Weights,
    ResNet50_Weights,
    VGG16_Weights,
)


# ──────────────────────────────────────────────────────────────────────────────
# Model builders
# ──────────────────────────────────────────────────────────────────────────────

NUM_CLASSES = 2  # NORMAL, PNEUMONIA
DROPOUT_RATE = 0.5


def _build_densenet121(pretrained: bool = True, freeze_backbone: bool = False) -> nn.Module:
    weights = DenseNet121_Weights.IMAGENET1K_V1 if pretrained else None
    model = tv_models.densenet121(weights=weights)
    if freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False
    in_features = model.classifier.in_features
    model.classifier = nn.Sequential(
        nn.Dropout(DROPOUT_RATE),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(DROPOUT_RATE / 2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model


def _build_efficientnet_b3(pretrained: bool = True, freeze_backbone: bool = False) -> nn.Module:
    weights = EfficientNet_B3_Weights.IMAGENET1K_V1 if pretrained else None
    model = tv_models.efficientnet_b3(weights=weights)
    if freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(DROPOUT_RATE),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(DROPOUT_RATE / 2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model


def _build_resnet50(pretrained: bool = True, freeze_backbone: bool = False) -> nn.Module:
    weights = ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
    model = tv_models.resnet50(weights=weights)
    if freeze_backbone:
        for name, p in model.named_parameters():
            if "layer4" not in name and "fc" not in name:
                p.requires_grad = False
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(DROPOUT_RATE),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(DROPOUT_RATE / 2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model


def _build_vgg16(pretrained: bool = True, freeze_backbone: bool = False) -> nn.Module:
    weights = VGG16_Weights.IMAGENET1K_V1 if pretrained else None
    model = tv_models.vgg16(weights=weights)
    if freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False
    in_features = model.classifier[6].in_features
    model.classifier[6] = nn.Sequential(
        nn.Dropout(DROPOUT_RATE),
        nn.Linear(in_features, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(DROPOUT_RATE / 2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model


MODEL_BUILDERS = {
    "DenseNet121":    _build_densenet121,
    "EfficientNetB3": _build_efficientnet_b3,
    "ResNet50":       _build_resnet50,
    "VGG16":          _build_vgg16,
}

# Layer name used by Grad-CAM for each architecture
GRADCAM_TARGET_LAYERS = {
    "DenseNet121":    "features.denseblock4.denselayer16.conv2",
    "EfficientNetB3": "features.8.0",
    "ResNet50":       "layer4.2.conv3",
    "VGG16":          "features.28",
}


# ──────────────────────────────────────────────────────────────────────────────
# Prediction result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PredictionResult:
    label: str                  # "NORMAL" | "PNEUMONIA"
    confidence: float           # 0.0 – 1.0
    pneumonia_probability: float
    normal_probability: float
    model_name: str
    inference_time_ms: float
    logits: np.ndarray


# ──────────────────────────────────────────────────────────────────────────────
# Model registry / loader
# ──────────────────────────────────────────────────────────────────────────────

class ClassificationModelRegistry:
    """Loads and caches all classification models."""

    LABELS = ["NORMAL", "PNEUMONIA"]

    def __init__(self, weights_dir: str | Path, device: Optional[str] = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.weights_dir = Path(weights_dir)
        self._models: Dict[str, nn.Module] = {}

    # ------------------------------------------------------------------
    def _load_or_init(self, name: str) -> nn.Module:
        if name in self._models:
            return self._models[name]

        model = MODEL_BUILDERS[name](pretrained=True)
        weight_path = self.weights_dir / f"{name.lower()}_best.pth"
        if weight_path.exists():
            state = torch.load(weight_path, map_location=self.device)
            # Support both raw state-dict and checkpoint dicts
            if "model_state_dict" in state:
                state = state["model_state_dict"]
            model.load_state_dict(state, strict=False)

        model.to(self.device).eval()
        self._models[name] = model
        return model

    # ------------------------------------------------------------------
    @torch.no_grad()
    def predict(
        self,
        tensor: np.ndarray,
        model_name: str = "DenseNet121",
    ) -> PredictionResult:
        """Run inference with a single model.

        tensor: float32 1×3×H×W numpy array (pre-processed).
        """
        model = self._load_or_init(model_name)
        x = torch.from_numpy(tensor).to(self.device)

        t0 = time.perf_counter()
        logits = model(x)
        probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()
        elapsed = (time.perf_counter() - t0) * 1000

        idx = int(np.argmax(probs))
        return PredictionResult(
            label=self.LABELS[idx],
            confidence=float(probs[idx]),
            pneumonia_probability=float(probs[1]),
            normal_probability=float(probs[0]),
            model_name=model_name,
            inference_time_ms=round(elapsed, 2),
            logits=logits.squeeze().cpu().numpy(),
        )

    # ------------------------------------------------------------------
    def available_models(self) -> List[str]:
        return list(MODEL_BUILDERS.keys())

    # ------------------------------------------------------------------
    def get_target_layer(self, model_name: str):
        """Return the conv layer object for Grad-CAM."""
        model = self._load_or_init(model_name)
        layer_name = GRADCAM_TARGET_LAYERS.get(model_name, "")
        layer = model
        for part in layer_name.split("."):
            try:
                layer = layer[int(part)] if part.isdigit() else getattr(layer, part)
            except (AttributeError, IndexError, TypeError):
                break
        return layer

    # ------------------------------------------------------------------
    def get_raw_model(self, model_name: str) -> nn.Module:
        return self._load_or_init(model_name)


# ──────────────────────────────────────────────────────────────────────────────
# Global singleton
# ──────────────────────────────────────────────────────────────────────────────

_registry: Optional[ClassificationModelRegistry] = None


def get_model_registry() -> ClassificationModelRegistry:
    global _registry
    if _registry is None:
        from app.config import settings
        _registry = ClassificationModelRegistry(
            weights_dir=settings.MODELS_DIR,
            device=settings.DEVICE,
        )
    return _registry
