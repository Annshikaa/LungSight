"""
Model benchmarking framework for LungSight AI.
Computes accuracy, precision, recall, F1, ROC-AUC, PR-AUC,
inference time, model size, parameter count, and FLOPs.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


# ──────────────────────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    specificity: float
    npv: float                      # negative predictive value
    avg_inference_time_ms: float
    model_size_mb: float
    parameter_count: int
    trainable_parameters: int
    confusion_matrix: List[List[int]]
    # Optional (require thop library)
    flops: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def count_parameters(model: nn.Module) -> Tuple[int, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def model_size_mb(model: nn.Module) -> float:
    total_bytes = sum(p.element_size() * p.numel() for p in model.parameters())
    return round(total_bytes / 1024 / 1024, 2)


def measure_inference_time(
    model: nn.Module,
    device: torch.device,
    input_size: Tuple[int, ...] = (1, 3, 224, 224),
    n_runs: int = 50,
    warmup: int = 5,
) -> float:
    """Average inference time in milliseconds over n_runs runs."""
    model.eval()
    dummy = torch.randn(*input_size, device=device)

    for _ in range(warmup):
        with torch.no_grad():
            model(dummy)

    if device.type == "cuda":
        torch.cuda.synchronize()

    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        with torch.no_grad():
            model(dummy)
        if device.type == "cuda":
            torch.cuda.synchronize()
        times.append((time.perf_counter() - t0) * 1000)

    return round(float(np.mean(times)), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Benchmarker
# ──────────────────────────────────────────────────────────────────────────────

class ModelBenchmarker:
    """Run all benchmark metrics for a given model on a test set."""

    def __init__(self, device: Optional[torch.device] = None):
        self.device = device or torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

    # ------------------------------------------------------------------
    def benchmark(
        self,
        model: nn.Module,
        model_name: str,
        test_tensors: List[np.ndarray],     # list of float32 1×3×H×W
        test_labels: List[int],             # 0=NORMAL, 1=PNEUMONIA
        threshold: float = 0.5,
    ) -> BenchmarkResult:

        model.eval()
        all_probs: List[float] = []

        for tensor in test_tensors:
            t = torch.from_numpy(tensor).to(self.device)
            with torch.no_grad():
                logits = model(t)
                prob   = torch.softmax(logits, dim=1)[0, 1].item()
            all_probs.append(prob)

        y_true = np.array(test_labels)
        y_prob = np.array(all_probs)
        y_pred = (y_prob >= threshold).astype(int)

        cm = confusion_matrix(y_true, y_pred).tolist()
        tn, fp, fn, tp = np.array(cm).ravel() if len(cm) == 2 else (0, 0, 0, 0)

        spec = tn / (tn + fp + 1e-7)
        npv  = tn / (tn + fn + 1e-7)

        inf_time = measure_inference_time(model, self.device)
        total_p, trainable_p = count_parameters(model)

        return BenchmarkResult(
            model_name=model_name,
            accuracy=round(float(accuracy_score(y_true, y_pred)), 4),
            precision=round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            recall=round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            f1_score=round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            roc_auc=round(float(roc_auc_score(y_true, y_prob)), 4),
            pr_auc=round(float(average_precision_score(y_true, y_prob)), 4),
            specificity=round(float(spec), 4),
            npv=round(float(npv), 4),
            avg_inference_time_ms=inf_time,
            model_size_mb=model_size_mb(model),
            parameter_count=total_p,
            trainable_parameters=trainable_p,
            confusion_matrix=cm,
        )

    # ------------------------------------------------------------------
    def benchmark_all(
        self,
        models: Dict[str, nn.Module],
        test_tensors: List[np.ndarray],
        test_labels: List[int],
    ) -> Dict[str, BenchmarkResult]:
        return {
            name: self.benchmark(model, name, test_tensors, test_labels)
            for name, model in models.items()
        }

    # ------------------------------------------------------------------
    @staticmethod
    def build_leaderboard(results: Dict[str, BenchmarkResult]) -> List[Dict]:
        rows = []
        for name, r in results.items():
            rows.append({
                "model": name,
                "accuracy": r.accuracy,
                "f1": r.f1_score,
                "roc_auc": r.roc_auc,
                "pr_auc": r.pr_auc,
                "inference_ms": r.avg_inference_time_ms,
                "size_mb": r.model_size_mb,
                "params_M": round(r.parameter_count / 1e6, 2),
            })
        return sorted(rows, key=lambda x: x["roc_auc"], reverse=True)
