"""
LungSight AI — Training Script
Trains DenseNet121, EfficientNetB3, ResNet50, VGG16 on chest X-ray dataset.
Supports mixed-precision, TensorBoard logging, early stopping, LR scheduling.

Usage:
    python train.py --model DenseNet121 --epochs 30 --data_dir ./data/chest_xray
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler

try:
    from torch.utils.tensorboard import SummaryWriter
except (AttributeError, ImportError):
    class SummaryWriter:
        def __init__(self, *args, **kwargs): pass
        def add_scalar(self, *args, **kwargs): pass
        def add_scalars(self, *args, **kwargs): pass
        def close(self): pass
from torchvision import transforms
from torchvision.datasets import ImageFolder

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.ml.models import MODEL_BUILDERS

# ──────────────────────────────────────────────────────────────────────────────
# Transforms
# ──────────────────────────────────────────────────────────────────────────────

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

train_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

val_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def build_weighted_sampler(dataset: ImageFolder) -> WeightedRandomSampler:
    """Oversample minority class to handle class imbalance."""
    class_counts = np.bincount(dataset.targets)
    class_weights = 1.0 / class_counts
    sample_weights = [class_weights[t] for t in dataset.targets]
    return WeightedRandomSampler(sample_weights, len(sample_weights))


def build_class_weights(dataset: ImageFolder, device: torch.device) -> torch.Tensor:
    counts = np.bincount(dataset.targets)
    weights = 1.0 / counts
    weights = weights / weights.sum() * len(counts)
    return torch.tensor(weights, dtype=torch.float32, device=device)


def accuracy(outputs: torch.Tensor, targets: torch.Tensor) -> float:
    preds = outputs.argmax(dim=1)
    return (preds == targets).float().mean().item()


# ──────────────────────────────────────────────────────────────────────────────
# Training loop
# ──────────────────────────────────────────────────────────────────────────────

def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    scaler,
    device: torch.device,
    epoch: int,
    writer,
) -> tuple[float, float]:
    model.train()
    total_loss, total_acc = 0.0, 0.0
    use_amp = device.type == "cuda"

    for i, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()

        with torch.cuda.amp.autocast(enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, labels)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item()
        total_acc  += accuracy(outputs.detach(), labels)

        if i % 50 == 0:
            step = epoch * len(loader) + i
            writer.add_scalar("train/step_loss", loss.item(), step)
            print(f"  [{i:4d}/{len(loader)}] loss: {loss.item():.4f}")

    n = len(loader)
    return total_loss / n, total_acc / n


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    model.eval()
    total_loss, total_acc = 0.0, 0.0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        total_loss += loss.item()
        total_acc  += accuracy(outputs, labels)
    n = len(loader)
    return total_loss / n, total_acc / n


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Train LungSight classification models")
    p.add_argument("--model",       type=str, default="DenseNet121",
                   choices=list(MODEL_BUILDERS.keys()))
    p.add_argument("--data_dir",    type=str, default="./data/chest_xray")
    p.add_argument("--epochs",      type=int, default=30)
    p.add_argument("--batch_size",  type=int, default=32)
    p.add_argument("--lr",          type=float, default=1e-4)
    p.add_argument("--weight_decay",type=float, default=1e-4)
    p.add_argument("--patience",    type=int, default=7)
    p.add_argument("--output_dir",  type=str, default="./backend/models/weights")
    p.add_argument("--freeze_backbone", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device} | Model: {args.model}")

    # ── Data ────────────────────────────────────────────────────────
    data_dir = Path(args.data_dir)
    train_ds = ImageFolder(data_dir / "train", transform=train_transforms)
    val_ds   = ImageFolder(data_dir / "val",   transform=val_transforms)
    test_ds  = ImageFolder(data_dir / "test",  transform=val_transforms)

    sampler = build_weighted_sampler(train_ds)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler,
                              num_workers=0, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False,
                              num_workers=0, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=args.batch_size, shuffle=False,
                              num_workers=0, pin_memory=True)

    print(f"Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")
    print(f"Classes: {train_ds.class_to_idx}")

    # ── Model ────────────────────────────────────────────────────────
    model = MODEL_BUILDERS[args.model](
        pretrained=True, freeze_backbone=args.freeze_backbone
    ).to(device)

    class_weights = build_class_weights(train_ds, device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)

    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    use_amp = device.type == "cuda"
    scaler  = torch.cuda.amp.GradScaler(enabled=use_amp)

    # ── Logging ──────────────────────────────────────────────────────
    log_dir = Path("./tb_logs") / args.model
    writer  = SummaryWriter(log_dir=str(log_dir))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Training loop ────────────────────────────────────────────────
    best_val_acc = 0.0
    patience_cnt = 0

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        print(f"\nEpoch [{epoch}/{args.epochs}]")

        tr_loss, tr_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, scaler, device, epoch, writer
        )
        va_loss, va_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"  Train — loss: {tr_loss:.4f}  acc: {tr_acc:.4f}")
        print(f"  Val   — loss: {va_loss:.4f}  acc: {va_acc:.4f}  [{time.time()-t0:.1f}s]")

        writer.add_scalars("loss", {"train": tr_loss, "val": va_loss}, epoch)
        writer.add_scalars("accuracy", {"train": tr_acc, "val": va_acc}, epoch)
        writer.add_scalar("lr", optimizer.param_groups[0]["lr"], epoch)

        if va_acc > best_val_acc:
            best_val_acc = va_acc
            patience_cnt = 0
            ckpt = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": va_acc,
                "val_loss": va_loss,
            }
            torch.save(model.state_dict(), out_dir / f"{args.model.lower()}_best.pth")
            torch.save(ckpt, out_dir / f"{args.model.lower()}_checkpoint.pth")
            print(f"  ✅ Saved best model (val_acc={va_acc:.4f})")
        else:
            patience_cnt += 1
            if patience_cnt >= args.patience:
                print(f"  ⏹  Early stopping triggered after {epoch} epochs.")
                break

    # ── Test evaluation ──────────────────────────────────────────────
    model.load_state_dict(torch.load(out_dir / f"{args.model.lower()}_best.pth"))
    te_loss, te_acc = evaluate(model, test_loader, criterion, device)
    print(f"\nTest — loss: {te_loss:.4f}  acc: {te_acc:.4f}")
    writer.add_scalar("test/accuracy", te_acc, 0)
    writer.close()

    print(f"\n✅ Training complete. Best val acc: {best_val_acc:.4f}")


if __name__ == "__main__":
    main()
