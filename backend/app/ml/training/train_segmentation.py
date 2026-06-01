"""
U-Net Lung Segmentation Training Script for LungSight AI.
Trains on a lung segmentation dataset (paired X-rays + binary masks).

Usage:
    python train_segmentation.py --data_dir ./data/lung_seg --epochs 50
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.ml.segmentation import UNetLungSegmenter, dice_score


class LungSegDataset(Dataset):
    def __init__(self, image_dir: Path, mask_dir: Path, size: int = 224):
        self.images = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))
        self.masks  = sorted(mask_dir.glob("*.png")) + sorted(mask_dir.glob("*.jpg"))
        self.size   = size
        assert len(self.images) == len(self.masks), "Image/mask count mismatch"

    def __len__(self): return len(self.images)

    def __getitem__(self, idx):
        img  = np.array(Image.open(self.images[idx]).convert("RGB").resize((self.size, self.size)))
        mask = np.array(Image.open(self.masks[idx]).convert("L").resize((self.size, self.size)))

        # Normalize image
        img  = img.astype(np.float32) / 255.0
        img  = (img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        img  = torch.from_numpy(img.transpose(2, 0, 1))

        # Binary mask
        mask = (mask > 127).astype(np.float32)
        mask = torch.from_numpy(mask).unsqueeze(0)
        return img, mask


def dice_loss(pred: torch.Tensor, target: torch.Tensor, eps: float = 1e-7) -> torch.Tensor:
    pred   = torch.sigmoid(pred)
    inter  = (pred * target).sum(dim=(2, 3))
    union  = pred.sum(dim=(2, 3)) + target.sum(dim=(2, 3))
    return 1 - (2 * inter + eps) / (union + eps)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data_dir",   default="./data/lung_seg")
    p.add_argument("--epochs",     type=int, default=50)
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--lr",         type=float, default=1e-4)
    p.add_argument("--output_dir", default="./backend/models/weights")
    args = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = Path(args.data_dir)
    out_dir  = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_ds = LungSegDataset(data_dir / "images/train", data_dir / "masks/train")
    val_ds   = LungSegDataset(data_dir / "images/val",   data_dir / "masks/val")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,  num_workers=4)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, num_workers=4)

    model     = UNetLungSegmenter().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    bce_loss  = nn.BCEWithLogitsLoss()

    best_dice = 0.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        for imgs, masks in train_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            optimizer.zero_grad()
            logits = model(imgs)
            loss = bce_loss(logits, masks) + dice_loss(logits, masks).mean()
            loss.backward()
            optimizer.step()

        # Validation
        model.eval()
        dice_scores = []
        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                preds = (torch.sigmoid(model(imgs)) > 0.5).float()
                for p, m in zip(preds.cpu().numpy(), masks.cpu().numpy()):
                    dice_scores.append(dice_score(
                        (p[0] * 255).astype(np.uint8),
                        (m[0] * 255).astype(np.uint8),
                    ))

        mean_dice = float(np.mean(dice_scores))
        print(f"Epoch [{epoch}/{args.epochs}]  Dice: {mean_dice:.4f}")
        scheduler.step(1 - mean_dice)

        if mean_dice > best_dice:
            best_dice = mean_dice
            torch.save(model.state_dict(), out_dir / "unet_lung_segmentation.pth")
            print(f"  ✅ Saved best model (Dice={mean_dice:.4f})")

    print(f"\n✅ Segmentation training done. Best Dice: {best_dice:.4f}")


if __name__ == "__main__":
    main()
