"""
Advanced chest X-ray preprocessing pipeline for LungSight AI.
Implements CLAHE, histogram equalization, contrast stretching,
gamma correction, noise reduction, and multi-stage augmentation.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageEnhance


# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

TARGET_SIZE = (224, 224)

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


# ──────────────────────────────────────────────────────────────────────────────
# Dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PreprocessedImage:
    original: np.ndarray          # uint8 H×W×3
    enhanced: np.ndarray          # uint8 H×W×3
    normalized: np.ndarray        # float32 H×W×3  (ImageNet-normalised)
    tensor_input: np.ndarray      # float32 1×3×H×W ready for PyTorch
    intermediate: Dict[str, np.ndarray]  # visualisation stages


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _to_uint8(img: np.ndarray) -> np.ndarray:
    """Clip and cast to uint8."""
    return np.clip(img, 0, 255).astype(np.uint8)


def _ensure_rgb(img: np.ndarray) -> np.ndarray:
    """Make sure image is H×W×3 RGB."""
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    elif img.shape[2] == 1:
        img = np.concatenate([img, img, img], axis=-1)
    elif img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def _resize(img: np.ndarray, size: Tuple[int, int] = TARGET_SIZE) -> np.ndarray:
    return cv2.resize(img, size, interpolation=cv2.INTER_LANCZOS4)


# ──────────────────────────────────────────────────────────────────────────────
# Enhancement steps
# ──────────────────────────────────────────────────────────────────────────────

def apply_clahe(img: np.ndarray, clip_limit: float = 3.0, tile_size: int = 8) -> np.ndarray:
    """Contrast Limited Adaptive Histogram Equalization on L channel."""
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    l_eq = clahe.apply(l)
    lab_eq = cv2.merge([l_eq, a, b])
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)


def apply_histogram_equalization(img: np.ndarray) -> np.ndarray:
    """Per-channel histogram equalization."""
    channels = cv2.split(img)
    eq = [cv2.equalizeHist(c) for c in channels]
    return cv2.merge(eq)


def apply_contrast_stretching(img: np.ndarray, p_low: float = 2.0, p_high: float = 98.0) -> np.ndarray:
    """Percentile-based contrast stretching."""
    result = np.zeros_like(img, dtype=np.float32)
    for i in range(3):
        lo, hi = np.percentile(img[:, :, i], [p_low, p_high])
        stretched = (img[:, :, i].astype(np.float32) - lo) / (hi - lo + 1e-7) * 255
        result[:, :, i] = np.clip(stretched, 0, 255)
    return _to_uint8(result)


def apply_gamma_correction(img: np.ndarray, gamma: float = 1.2) -> np.ndarray:
    lut = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)], dtype=np.uint8)
    return cv2.LUT(img, lut)


def apply_gaussian_blur(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    return cv2.GaussianBlur(img, (ksize, ksize), 0)


def apply_median_blur(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    return cv2.medianBlur(img, ksize)


def apply_sharpening(img: np.ndarray, strength: float = 1.5) -> np.ndarray:
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]], dtype=np.float32) * strength
    kernel[1, 1] = 1 + 8 * strength
    kernel /= kernel.sum()
    return _to_uint8(cv2.filter2D(img.astype(np.float32), -1, kernel))


def apply_adaptive_thresholding(img: np.ndarray) -> np.ndarray:
    """For visualization only — shows lung boundaries."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return cv2.cvtColor(adaptive, cv2.COLOR_GRAY2RGB)


# ──────────────────────────────────────────────────────────────────────────────
# Normalisation
# ──────────────────────────────────────────────────────────────────────────────

def normalize_imagenet(img: np.ndarray) -> np.ndarray:
    """Float32 H×W×3 in [0,1], then ImageNet-normalised."""
    x = img.astype(np.float32) / 255.0
    return (x - IMAGENET_MEAN) / IMAGENET_STD


def to_tensor(img_normalized: np.ndarray) -> np.ndarray:
    """H×W×3 → 1×3×H×W (PyTorch layout)."""
    return img_normalized.transpose(2, 0, 1)[np.newaxis, ...]


# ──────────────────────────────────────────────────────────────────────────────
# Augmentation (training only)
# ──────────────────────────────────────────────────────────────────────────────

def augment_training(img: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
    """Random augmentation for training data."""
    rng = np.random.default_rng(seed)

    # Random horizontal flip
    if rng.random() < 0.5:
        img = np.fliplr(img)

    # Random rotation ±15°
    angle = rng.uniform(-15, 15)
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT_101)

    # Random brightness / contrast shift
    pil = Image.fromarray(img)
    pil = ImageEnhance.Brightness(pil).enhance(rng.uniform(0.8, 1.2))
    pil = ImageEnhance.Contrast(pil).enhance(rng.uniform(0.8, 1.2))
    img = np.array(pil)

    # Random zoom (crop + resize)
    if rng.random() < 0.3:
        zoom = rng.uniform(0.85, 1.0)
        h, w = img.shape[:2]
        ch, cw = int(h * zoom), int(w * zoom)
        y0 = rng.integers(0, h - ch)
        x0 = rng.integers(0, w - cw)
        img = img[y0:y0 + ch, x0:x0 + cw]
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LANCZOS4)

    return img


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────────────────────────────────────

class XRayPreprocessor:
    """Full preprocessing pipeline for a single chest X-ray image."""

    def __init__(
        self,
        target_size: Tuple[int, int] = TARGET_SIZE,
        use_clahe: bool = True,
        use_gamma: bool = True,
        use_sharpen: bool = True,
        use_denoise: bool = True,
        training_mode: bool = False,
    ):
        self.target_size = target_size
        self.use_clahe = use_clahe
        self.use_gamma = use_gamma
        self.use_sharpen = use_sharpen
        self.use_denoise = use_denoise
        self.training_mode = training_mode

    # ------------------------------------------------------------------
    def _load(self, source) -> np.ndarray:
        """Accept file path, bytes, PIL Image, or numpy array."""
        if isinstance(source, np.ndarray):
            img = source
        elif isinstance(source, Image.Image):
            img = np.array(source.convert("RGB"))
        elif isinstance(source, (bytes, bytearray)):
            pil = Image.open(io.BytesIO(source)).convert("RGB")
            img = np.array(pil)
        else:
            pil = Image.open(source).convert("RGB")
            img = np.array(pil)
        return _ensure_rgb(img)

    # ------------------------------------------------------------------
    def process(self, source) -> PreprocessedImage:
        stages: Dict[str, np.ndarray] = {}

        # 1. Load & resize
        raw = self._load(source)
        original = _resize(raw, self.target_size)
        stages["original"] = original.copy()

        # 2. Contrast stretching
        img = apply_contrast_stretching(original)
        stages["contrast_stretched"] = img.copy()

        # 3. CLAHE
        if self.use_clahe:
            img = apply_clahe(img)
            stages["clahe"] = img.copy()

        # 4. Gamma correction
        if self.use_gamma:
            img = apply_gamma_correction(img, gamma=1.15)
            stages["gamma"] = img.copy()

        # 5. Noise reduction
        if self.use_denoise:
            img = apply_median_blur(img, ksize=3)
            stages["denoised"] = img.copy()

        # 6. Sharpening
        if self.use_sharpen:
            img = apply_sharpening(img, strength=0.5)
            stages["sharpened"] = img.copy()

        enhanced = img.copy()
        stages["enhanced"] = enhanced.copy()

        # 7. Training augmentation
        if self.training_mode:
            img = augment_training(img)
            stages["augmented"] = img.copy()

        # 8. Adaptive thresholding for visualisation
        stages["adaptive_threshold"] = apply_adaptive_thresholding(original)

        # 9. Normalise + tensor
        normalized = normalize_imagenet(img)
        tensor = to_tensor(normalized)

        return PreprocessedImage(
            original=original,
            enhanced=enhanced,
            normalized=normalized,
            tensor_input=tensor,
            intermediate=stages,
        )

    # ------------------------------------------------------------------
    def process_batch(self, sources) -> list[PreprocessedImage]:
        return [self.process(s) for s in sources]


# Singleton for inference
inference_preprocessor = XRayPreprocessor(training_mode=False)
train_preprocessor = XRayPreprocessor(training_mode=True)
