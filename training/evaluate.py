"""
LungSight AI — Comprehensive Model Evaluation Script
Generates confusion matrices, ROC curves, PR curves, calibration curves,
and misclassification analysis for all trained models.

Usage:
    python evaluate.py --model DenseNet121 --data_dir ./data/chest_xray
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    RocCurveDisplay,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.ml.models import MODEL_BUILDERS

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

val_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model",       default="DenseNet121", choices=list(MODEL_BUILDERS.keys()))
    p.add_argument("--data_dir",    default="./data/chest_xray")
    p.add_argument("--weights_dir", default="./backend/models/weights")
    p.add_argument("--output_dir",  default="./research/results")
    p.add_argument("--batch_size",  type=int, default=32)
    return p.parse_args()


@torch.no_grad()
def get_predictions(model, loader, device):
    model.eval()
    all_probs, all_labels = [], []
    for imgs, labels in loader:
        imgs = imgs.to(device)
        probs = torch.softmax(model(imgs), dim=1)[:, 1].cpu().numpy()
        all_probs.extend(probs.tolist())
        all_labels.extend(labels.numpy().tolist())
    return np.array(all_probs), np.array(all_labels)


def plot_confusion_matrix(y_true, y_pred, labels, out_path):
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_roc_curve(y_true, y_prob, model_name, out_path):
    fig, ax = plt.subplots(figsize=(6, 5))
    RocCurveDisplay.from_predictions(y_true, y_prob, ax=ax, name=model_name)
    ax.plot([0, 1], [0, 1], "k--", lw=0.8)
    ax.set_title(f"ROC Curve — {model_name}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_pr_curve(y_true, y_prob, model_name, out_path):
    fig, ax = plt.subplots(figsize=(6, 5))
    PrecisionRecallDisplay.from_predictions(y_true, y_prob, ax=ax, name=model_name)
    ax.set_title(f"Precision-Recall Curve — {model_name}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_calibration_curve(y_true, y_prob, model_name, out_path):
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(prob_pred, prob_true, "s-", label=model_name, color="#0ea5e9")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="Perfect calibration")
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Fraction of Positives")
    ax.set_title(f"Calibration Curve — {model_name}", fontsize=13, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out_dir = Path(args.output_dir) / args.model
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    test_ds = ImageFolder(Path(args.data_dir) / "test", transform=val_transforms)
    loader  = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=4)
    class_names = [c for c, _ in sorted(test_ds.class_to_idx.items(), key=lambda x: x[1])]

    # Load model
    model = MODEL_BUILDERS[args.model](pretrained=False)
    w = Path(args.weights_dir) / f"{args.model.lower()}_best.pth"
    if w.exists():
        model.load_state_dict(torch.load(w, map_location=device))
        print(f"✅ Loaded weights from {w}")
    else:
        print(f"⚠️  No weights found at {w}. Using random weights.")
    model.to(device)

    # Predict
    y_prob, y_true = get_predictions(model, loader, device)
    y_pred = (y_prob >= 0.5).astype(int)

    # Classification report
    report = classification_report(y_true, y_pred, target_names=class_names, digits=4)
    print(f"\n{args.model} Evaluation:\n{'='*60}")
    print(report)
    print(f"ROC-AUC: {roc_auc_score(y_true, y_prob):.4f}")
    (out_dir / "classification_report.txt").write_text(report)

    # Plots
    plot_confusion_matrix(y_true, y_pred, class_names, out_dir / "confusion_matrix.png")
    plot_roc_curve(y_true, y_prob, args.model, out_dir / "roc_curve.png")
    plot_pr_curve(y_true, y_prob, args.model, out_dir / "pr_curve.png")
    plot_calibration_curve(y_true, y_prob, args.model, out_dir / "calibration_curve.png")

    print(f"\n✅ Evaluation plots saved to {out_dir}")


if __name__ == "__main__":
    main()
