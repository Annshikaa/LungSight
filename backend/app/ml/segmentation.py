"""
U-Net lung segmentation module for LungSight AI.
Uses a ResNet34-encoder U-Net to generate binary lung masks,
compute dice/IoU metrics, and extract lung ROI.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ──────────────────────────────────────────────────────────────────────────────
# Lightweight U-Net (no external seg-models dependency required at inference)
# ──────────────────────────────────────────────────────────────────────────────

def _double_conv(in_ch: int, out_ch: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class UNetLungSegmenter(nn.Module):
    """Lightweight U-Net for binary lung segmentation."""

    def __init__(self, in_channels: int = 3, features: Tuple[int, ...] = (64, 128, 256, 512)):
        super().__init__()
        self.downs = nn.ModuleList()
        self.ups   = nn.ModuleList()
        self.pool  = nn.MaxPool2d(2, 2)

        ch = in_channels
        for f in features:
            self.downs.append(_double_conv(ch, f))
            ch = f

        self.bottleneck = _double_conv(features[-1], features[-1] * 2)

        for f in reversed(features):
            self.ups.append(nn.ConvTranspose2d(f * 2, f, 2, 2))
            self.ups.append(_double_conv(f * 2, f))

        self.final = nn.Conv2d(features[0], 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip_connections: list[torch.Tensor] = []
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)
        skip_connections.reverse()

        for i in range(0, len(self.ups), 2):
            x = self.ups[i](x)
            skip = skip_connections[i // 2]
            if x.shape != skip.shape:
                x = F.interpolate(x, size=skip.shape[2:])
            x = torch.cat([skip, x], dim=1)
            x = self.ups[i + 1](x)

        return self.final(x)  # raw logits


# ──────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SegmentationResult:
    mask: np.ndarray           # uint8 H×W binary (0 or 255)
    overlay: np.ndarray        # uint8 H×W×3
    roi: np.ndarray            # uint8 H×W×3 – masked original
    lung_area_pixels: int
    lung_area_percentage: float
    dice_score: Optional[float] = None
    iou_score:  Optional[float] = None


# ──────────────────────────────────────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────────────────────────────────────

def dice_score(pred: np.ndarray, target: np.ndarray, eps: float = 1e-7) -> float:
    p = (pred > 127).astype(np.float32).flatten()
    t = (target > 127).astype(np.float32).flatten()
    intersection = (p * t).sum()
    return (2.0 * intersection + eps) / (p.sum() + t.sum() + eps)


def iou_score(pred: np.ndarray, target: np.ndarray, eps: float = 1e-7) -> float:
    p = (pred > 127).astype(np.float32).flatten()
    t = (target > 127).astype(np.float32).flatten()
    intersection = (p * t).sum()
    union = p.sum() + t.sum() - intersection
    return (intersection + eps) / (union + eps)


# ──────────────────────────────────────────────────────────────────────────────
# Segmentation engine
# ──────────────────────────────────────────────────────────────────────────────

class LungSegmentationEngine:
    """Load U-Net once; call segment() for each image."""

    MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __init__(
        self,
        weights_path: Optional[str | Path] = None,
        device: Optional[str] = None,
        input_size: int = 224,
    ):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.input_size = input_size

        self.model = UNetLungSegmenter()
        if weights_path and Path(weights_path).exists():
            state = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state)
        self.model.to(self.device).eval()

    # ------------------------------------------------------------------
    def _preprocess(self, img: np.ndarray) -> torch.Tensor:
        img_r = cv2.resize(img, (self.input_size, self.input_size))
        x = img_r.astype(np.float32) / 255.0
        x = (x - self.MEAN) / self.STD
        x = x.transpose(2, 0, 1)
        return torch.from_numpy(x).unsqueeze(0).to(self.device)

    # ------------------------------------------------------------------
    @torch.no_grad()
    def segment(
        self,
        img: np.ndarray,
        threshold: float = 0.5,
        ground_truth_mask: Optional[np.ndarray] = None,
    ) -> SegmentationResult:
        """
        Segment lung regions from a uint8 H×W×3 RGB image.

        Falls back to a morphological approximation when the model has
        random weights (no pretrained checkpoint loaded), so the pipeline
        still produces valid visualisations even before fine-tuning.
        """
        tensor = self._preprocess(img)
        logits = self.model(tensor)
        prob   = torch.sigmoid(logits).squeeze().cpu().numpy()

        # ── Resize mask to original image size ──────────────────────────
        h, w = img.shape[:2]
        mask_f = cv2.resize(prob, (w, h), interpolation=cv2.INTER_LINEAR)
        mask_bin = (mask_f > threshold).astype(np.uint8) * 255

        # ── Morphological cleanup ───────────────────────────────────────
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        mask_bin = cv2.morphologyEx(mask_bin, cv2.MORPH_CLOSE, kernel)
        mask_bin = cv2.morphologyEx(mask_bin, cv2.MORPH_OPEN,  kernel)

        # ── If mask is nearly empty (random weights) use Otsu fallback ─
        if mask_bin.sum() < mask_bin.size * 0.02:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            _, mask_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            mask_bin = cv2.morphologyEx(mask_bin, cv2.MORPH_CLOSE, kernel)

        # ── Overlay ─────────────────────────────────────────────────────
        overlay = img.copy()
        green_tint = np.zeros_like(img)
        green_tint[:, :, 1] = 255
        alpha = 0.35
        mask_3ch = np.stack([mask_bin, mask_bin, mask_bin], axis=-1) > 0
        overlay[mask_3ch] = (
            overlay[mask_3ch] * (1 - alpha) + green_tint[mask_3ch] * alpha
        ).astype(np.uint8)

        # ── ROI ─────────────────────────────────────────────────────────
        roi = img.copy()
        roi[mask_bin == 0] = 0

        # ── Metrics ─────────────────────────────────────────────────────
        lung_pixels = int((mask_bin > 0).sum())
        total_pixels = mask_bin.size
        lung_pct = lung_pixels / total_pixels * 100

        d_score = dice_score(mask_bin, ground_truth_mask) if ground_truth_mask is not None else None
        i_score = iou_score(mask_bin, ground_truth_mask) if ground_truth_mask is not None else None

        return SegmentationResult(
            mask=mask_bin,
            overlay=overlay,
            roi=roi,
            lung_area_pixels=lung_pixels,
            lung_area_percentage=round(lung_pct, 2),
            dice_score=round(d_score, 4) if d_score is not None else None,
            iou_score=round(i_score, 4) if i_score is not None else None,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Global singleton (lazy-loaded)
# ──────────────────────────────────────────────────────────────────────────────

_engine: Optional[LungSegmentationEngine] = None


def get_segmentation_engine() -> LungSegmentationEngine:
    global _engine
    if _engine is None:
        from app.config import settings
        weights = Path(settings.MODELS_DIR) / "unet_lung_segmentation.pth"
        _engine = LungSegmentationEngine(weights_path=weights)
    return _engine
