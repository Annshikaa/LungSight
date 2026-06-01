"""
Explainable AI module for LungSight AI.
Implements Grad-CAM, Grad-CAM++, Saliency Maps, and Integrated Gradients.
Generates heatmaps, overlays, bounding boxes, and activation maps.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn


# ──────────────────────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ExplainabilityResult:
    method: str
    heatmap: np.ndarray          # float32 H×W in [0,1]
    heatmap_colored: np.ndarray  # uint8  H×W×3 (JET colormap)
    overlay: np.ndarray          # uint8  H×W×3 heatmap blended over original
    bounding_box: Optional[Tuple[int, int, int, int]]  # x,y,w,h
    activation_coverage: float   # fraction of image covered by high-activation
    attention_map: np.ndarray    # same as heatmap_colored (for dashboard)


# ──────────────────────────────────────────────────────────────────────────────
# Hook helpers
# ──────────────────────────────────────────────────────────────────────────────

class _ActivationGradHook:
    def __init__(self):
        self.activation: Optional[torch.Tensor] = None
        self.gradient:   Optional[torch.Tensor] = None
        self._handles = []

    def register(self, layer: nn.Module):
        self._handles.append(layer.register_forward_hook(self._save_activation))
        self._handles.append(layer.register_full_backward_hook(self._save_gradient))

    def _save_activation(self, module, input, output):
        self.activation = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradient = grad_output[0].detach()

    def remove(self):
        for h in self._handles:
            h.remove()


# ──────────────────────────────────────────────────────────────────────────────
# Post-processing
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_heatmap(cam: np.ndarray) -> np.ndarray:
    cam = np.maximum(cam, 0)
    mn, mx = cam.min(), cam.max()
    if mx - mn < 1e-8:
        return np.zeros_like(cam, dtype=np.float32)
    return ((cam - mn) / (mx - mn)).astype(np.float32)


def _resize_heatmap(cam: np.ndarray, target_hw: Tuple[int, int]) -> np.ndarray:
    return cv2.resize(cam, (target_hw[1], target_hw[0]), interpolation=cv2.INTER_CUBIC)


def _colorize(cam_norm: np.ndarray) -> np.ndarray:
    colored = cv2.applyColorMap((cam_norm * 255).astype(np.uint8), cv2.COLORMAP_JET)
    return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)


def _blend_overlay(
    original_rgb: np.ndarray,
    heatmap_colored: np.ndarray,
    alpha: float = 0.45,
) -> np.ndarray:
    orig = cv2.resize(original_rgb, (heatmap_colored.shape[1], heatmap_colored.shape[0]))
    overlay = (orig.astype(np.float32) * (1 - alpha) + heatmap_colored.astype(np.float32) * alpha)
    return np.clip(overlay, 0, 255).astype(np.uint8)


def _bounding_box(cam_norm: np.ndarray, threshold: float = 0.4) -> Optional[Tuple[int, int, int, int]]:
    binary = (cam_norm > threshold).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(largest)  # x, y, w, h


def _activation_coverage(cam_norm: np.ndarray, threshold: float = 0.4) -> float:
    return float((cam_norm > threshold).mean())


# ──────────────────────────────────────────────────────────────────────────────
# Grad-CAM
# ──────────────────────────────────────────────────────────────────────────────

class GradCAM:
    """Standard Grad-CAM."""

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.hook = _ActivationGradHook()
        self.hook.register(target_layer)

    def generate(
        self,
        tensor: torch.Tensor,   # 1×C×H×W
        class_idx: Optional[int] = None,
        original_hw: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """Return normalised float32 H×W heatmap."""
        self.model.zero_grad()
        tensor = tensor.requires_grad_(True)
        output = self.model(tensor)

        if class_idx is None:
            class_idx = int(output.argmax(dim=1))

        score = output[0, class_idx]
        score.backward()

        grad = self.hook.gradient         # 1×C×h×w
        act  = self.hook.activation       # 1×C×h×w

        weights = grad.mean(dim=(2, 3), keepdim=True)
        cam = (weights * act).sum(dim=1).squeeze().cpu().numpy()
        return _normalize_heatmap(cam)

    def cleanup(self):
        self.hook.remove()


# ──────────────────────────────────────────────────────────────────────────────
# Grad-CAM++
# ──────────────────────────────────────────────────────────────────────────────

class GradCAMPlusPlus(GradCAM):
    """Grad-CAM++ with second-order gradient weighting."""

    def generate(
        self,
        tensor: torch.Tensor,
        class_idx: Optional[int] = None,
        original_hw: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        self.model.zero_grad()
        tensor = tensor.requires_grad_(True)
        output = self.model(tensor)

        if class_idx is None:
            class_idx = int(output.argmax(dim=1))

        score = output[0, class_idx]
        score.backward()

        grad = self.hook.gradient.squeeze().cpu().numpy()  # C×h×w
        act  = self.hook.activation.squeeze().cpu().numpy()

        # Second-order weights
        alpha_num   = grad ** 2
        alpha_denom = 2 * grad ** 2 + (act * grad ** 3).sum(axis=(1, 2), keepdims=True) + 1e-7
        alpha = alpha_num / alpha_denom
        weights = (alpha * np.maximum(grad, 0)).sum(axis=(1, 2))

        cam = (weights[:, None, None] * act).sum(axis=0)
        return _normalize_heatmap(cam)


# ──────────────────────────────────────────────────────────────────────────────
# Vanilla Saliency
# ──────────────────────────────────────────────────────────────────────────────

def compute_saliency(
    model: nn.Module,
    tensor: torch.Tensor,
    class_idx: Optional[int] = None,
) -> np.ndarray:
    """Vanilla gradient saliency map."""
    model.zero_grad()
    tensor = tensor.clone().requires_grad_(True)
    output = model(tensor)

    if class_idx is None:
        class_idx = int(output.argmax(dim=1))

    output[0, class_idx].backward()
    saliency = tensor.grad.data.abs().squeeze().cpu().numpy()  # 3×H×W
    saliency = saliency.max(axis=0)  # H×W
    return _normalize_heatmap(saliency)


# ──────────────────────────────────────────────────────────────────────────────
# Integrated Gradients
# ──────────────────────────────────────────────────────────────────────────────

def compute_integrated_gradients(
    model: nn.Module,
    tensor: torch.Tensor,
    class_idx: Optional[int] = None,
    steps: int = 50,
) -> np.ndarray:
    """Integrated Gradients attribution."""
    model.zero_grad()
    baseline = torch.zeros_like(tensor)

    if class_idx is None:
        with torch.no_grad():
            class_idx = int(model(tensor).argmax(dim=1))

    alphas = torch.linspace(0.0, 1.0, steps, device=tensor.device)
    grads = []
    for alpha in alphas:
        x = baseline + alpha * (tensor - baseline)
        x = x.clone().requires_grad_(True)
        out = model(x)
        out[0, class_idx].backward()
        grads.append(x.grad.detach().cpu().numpy())

    avg_grads = np.mean(grads, axis=0)          # 1×3×H×W
    ig = ((tensor.cpu().numpy() - baseline.cpu().numpy()) * avg_grads).squeeze()
    ig_map = np.abs(ig).max(axis=0)             # H×W
    return _normalize_heatmap(ig_map)


# ──────────────────────────────────────────────────────────────────────────────
# Unified explainability engine
# ──────────────────────────────────────────────────────────────────────────────

class ExplainabilityEngine:
    """Run all XAI methods and return full result set."""

    def __init__(self, model: nn.Module, target_layer: nn.Module, device: torch.device):
        self.model = model
        self.target_layer = target_layer
        self.device = device

    # ------------------------------------------------------------------
    def explain(
        self,
        tensor: np.ndarray,         # float32 1×3×H×W
        original_image: np.ndarray, # uint8 H×W×3
        class_idx: Optional[int] = None,
        methods: Optional[List[str]] = None,
    ) -> Dict[str, ExplainabilityResult]:
        if methods is None:
            methods = ["gradcam", "gradcam_pp", "saliency", "integrated_gradients"]

        t = torch.from_numpy(tensor).to(self.device)
        hw = (original_image.shape[0], original_image.shape[1])
        results: Dict[str, ExplainabilityResult] = {}

        # ── Grad-CAM ────────────────────────────────────────────────────
        if "gradcam" in methods:
            gc = GradCAM(self.model, self.target_layer)
            cam = gc.generate(t.clone(), class_idx)
            gc.cleanup()
            results["gradcam"] = self._build_result("gradcam", cam, original_image, hw)

        # ── Grad-CAM++ ───────────────────────────────────────────────────
        if "gradcam_pp" in methods:
            gcpp = GradCAMPlusPlus(self.model, self.target_layer)
            cam  = gcpp.generate(t.clone(), class_idx)
            gcpp.cleanup()
            results["gradcam_pp"] = self._build_result("gradcam_pp", cam, original_image, hw)

        # ── Saliency ─────────────────────────────────────────────────────
        if "saliency" in methods:
            cam = compute_saliency(self.model, t.clone(), class_idx)
            results["saliency"] = self._build_result("saliency", cam, original_image, hw)

        # ── Integrated Gradients ─────────────────────────────────────────
        if "integrated_gradients" in methods:
            cam = compute_integrated_gradients(self.model, t.clone(), class_idx)
            results["integrated_gradients"] = self._build_result(
                "integrated_gradients", cam, original_image, hw
            )

        return results

    # ------------------------------------------------------------------
    def _build_result(
        self,
        method: str,
        cam_norm: np.ndarray,
        original_image: np.ndarray,
        hw: Tuple[int, int],
    ) -> ExplainabilityResult:
        cam_resized  = _resize_heatmap(cam_norm, hw)
        cam_colored  = _colorize(cam_resized)
        overlay      = _blend_overlay(original_image, cam_colored)
        bbox         = _bounding_box(cam_resized)
        coverage     = _activation_coverage(cam_resized)

        return ExplainabilityResult(
            method=method,
            heatmap=cam_resized,
            heatmap_colored=cam_colored,
            overlay=overlay,
            bounding_box=bbox,
            activation_coverage=round(coverage, 4),
            attention_map=cam_colored,
        )
