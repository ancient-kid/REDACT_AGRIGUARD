# train_torch_fixed_amp.py
"""
Stable PyTorch training + eval script
- Requires: torch >= 2.x, torchvision
- Designed for torch 2.7.1+cu118 (uses torch.amp)
- Folder layout expected:
    data/
      train/
        ClassA/
        ClassB/
      val/
        ClassA/
        ClassB/
"""
import os
import math
import time
import random
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd
from PIL import Image

import torch
from torch import nn, optim
from torch import amp
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import torchvision.transforms as T
from torchvision import models

# ----------------------------
# User config
# ----------------------------
DATA_ROOT = Path("data")
TRAIN_DIR = DATA_ROOT / "train"
VAL_DIR = DATA_ROOT / "valid"

IMG_SIZE = 224
BATCH_SIZE = 32
NUM_WORKERS = 4
EPOCHS = 8
LR = 1e-3
WEIGHT_DECAY = 1e-4
SEED = 42
SAVE_BEST = Path("best_model.pth")
DEBUG = False        # set True for fast iteration
DEBUG_N = 8000       # number of samples if DEBUG=True
PRINT_EVERY = 100    # steps
POS_WEIGHT_ENABLED = True  # use pos weight for BCEWithLogitsLoss

# ----------------------------
# Determinism
# ----------------------------
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

# ----------------------------
# Device detection
# ----------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")
print("Torch version:", torch.__version__)
if DEVICE.type == "cuda":
    try:
        print("GPU Name:", torch.cuda.get_device_name(0))
        print("CUDA device count:", torch.cuda.device_count())
    except Exception:
        pass

# ----------------------------
# Dataset: binary label (healthy=1, diseased=0)
# ----------------------------
class BinaryFolderDataset(Dataset):
    def __init__(self, root_dir: Path, img_size=IMG_SIZE, transform=None):
        self.root_dir = Path(root_dir)
        if not self.root_dir.exists():
            raise FileNotFoundError(f"{root_dir} not found")
        self.items = []
        for cls_name in sorted([d.name for d in self.root_dir.iterdir() if d.is_dir()]):
            cls_dir = self.root_dir / cls_name
            for f in cls_dir.iterdir():
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    # label: healthy -> 1, otherwise diseased -> 0
                    is_healthy = ("healthy" in cls_name.lower())
                    label = 1 if is_healthy else 0
                    self.items.append((str(f), label, cls_name))
        self.transform = transform or T.Compose([
            T.Resize((img_size, img_size)),
            T.RandomHorizontalFlip(),
            T.RandomRotation(8),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406],
                        [0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        path, label, cls = self.items[idx]
        img = Image.open(path).convert("RGB")
        img = self.transform(img)
        return img, torch.tensor(label, dtype=torch.float32), path

# ----------------------------
# Simple CNN (matching your earlier SimpleCNN)
# ----------------------------
class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(128, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x).view(x.size(0), -1)
        x = self.classifier(x)
        return x  # raw logits (B,1)

# ----------------------------
# Build datasets + loaders
# ----------------------------
def build_loaders(train_dir, val_dir, batch_size=BATCH_SIZE, debug=DEBUG) -> Tuple[DataLoader, DataLoader, dict]:
    train_ds = BinaryFolderDataset(train_dir)
    val_ds = BinaryFolderDataset(val_dir, transform=T.Compose([
        T.Resize((IMG_SIZE, IMG_SIZE)),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406],
                    [0.229, 0.224, 0.225]),
    ]))

    if debug:
        # sample subset
        train_items = random.sample(train_ds.items, min(DEBUG_N, len(train_ds)))
        train_ds.items = train_items
        val_items = random.sample(val_ds.items, min(2048, len(val_ds)))
        val_ds.items = val_items
        print(f"[DEBUG] train samples: {len(train_ds)}, val samples: {len(val_ds)}")

    # compute class counts and create sampler to balance training
    labels = [lbl for _, lbl, _ in train_ds.items]
    counts = {0: 0, 1: 0}
    for x in labels:
        counts[int(x)] += 1
    print("Train class counts:", counts)

    # Weighted sampler (optional). If dataset is imbalanced, sampler helps.
    class_sample_count = [counts[0], counts[1]]
    weights = []
    total = float(len(labels))
    # inverse freq per label
    for lbl in labels:
        weights.append(1.0 / (class_sample_count[int(lbl)] + 1e-9))
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler,
                              num_workers=NUM_WORKERS, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=NUM_WORKERS, pin_memory=True)

    metadata = {"train_counts": counts, "n_train": len(train_ds), "n_val": len(val_ds)}
    return train_loader, val_loader, metadata

# ----------------------------
# Metrics helpers
# ----------------------------
def binary_metrics(y_true: np.ndarray, y_prob: np.ndarray, thresh=0.5):
    y_pred = (y_prob >= thresh).astype(int)
    from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score,
                                 recall_score, f1_score, roc_auc_score, confusion_matrix)
    acc = accuracy_score(y_true, y_pred)
    bal = balanced_accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_prob)
    except Exception:
        auc = float("nan")
    cm = confusion_matrix(y_true, y_pred)
    return {"acc": acc, "bal": bal, "prec": prec, "rec": rec, "f1": f1, "auc": auc, "cm": cm}

# ----------------------------
# Train / Eval loops with new amp API
# ----------------------------
def train_one_epoch(model, loader, optimizer, criterion, scaler, epoch_idx, total_epochs):
    model.train()
    running_loss = 0.0
    n = 0
    use_amp = (DEVICE.type == "cuda")
    for batch_idx, (imgs, labels, _) in enumerate(loader):
        imgs = imgs.to(DEVICE, non_blocking=True)
        labels = labels.to(DEVICE, non_blocking=True).unsqueeze(1)  # shape (B,1)

        optimizer.zero_grad()
        with amp.autocast("cuda", enabled=use_amp):
            logits = model(imgs)
            loss = criterion(logits, labels)

        if scaler is not None:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        cur_loss = loss.item()
        running_loss += cur_loss * imgs.size(0)
        n += imgs.size(0)

        if (batch_idx + 1) % PRINT_EVERY == 0:
            print(f"  [Epoch {epoch_idx+1}/{total_epochs}] Step {batch_idx+1}/{len(loader)} loss={cur_loss:.4f}")

    return running_loss / max(1, n)

def evaluate(model, loader):
    model.eval()
    probs_list = []
    labels_list = []
    paths_list = []
    use_amp = (DEVICE.type == "cuda")
    with torch.no_grad():
        for imgs, labels, paths in loader:
            imgs = imgs.to(DEVICE, non_blocking=True)
            with amp.autocast("cuda", enabled=use_amp):
                logits = model(imgs)
                probs = torch.sigmoid(logits).cpu().numpy().ravel()
            probs_list.append(probs)
            labels_list.append(labels.numpy().ravel())
            paths_list.extend(paths)
    probs_all = np.concatenate(probs_list) if len(probs_list) else np.array([])
    labels_all = np.concatenate(labels_list) if len(labels_list) else np.array([])
    return labels_all, probs_all, paths_list

# ----------------------------
# Main
# ----------------------------
def main():
    train_loader, val_loader, meta = build_loaders(TRAIN_DIR, VAL_DIR, batch_size=BATCH_SIZE, debug=DEBUG)

    model = SimpleCNN().to(DEVICE)
    print(model)

    # compute pos_weight for BCEWithLogitsLoss
    train_counts = meta["train_counts"]
    pos_weight = None
    if POS_WEIGHT_ENABLED:
        # pos_weight is applied to positive class (healthy=1) to up-weight minority if present
        # typical formula: total / (2 * count_pos)
        cnt_pos = max(1, train_counts.get(1, 0))
        cnt_neg = max(1, train_counts.get(0, 0))
        pos_weight_val = cnt_neg / cnt_pos
        pos_weight = torch.tensor([pos_weight_val], dtype=torch.float32, device=DEVICE)
        print("pos_weight:", float(pos_weight.item()))

    if pos_weight is not None:
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    else:
        criterion = nn.BCEWithLogitsLoss()

    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    # scheduler (optional)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    # AMP scaler (new API)
    scaler = amp.GradScaler(device="cuda" if DEVICE.type == "cuda" else "cpu") if DEVICE.type == "cuda" else None

    best_f1 = -1.0
    for epoch in range(EPOCHS):
        t0 = time.time()
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, scaler, epoch, EPOCHS)
        scheduler.step()

        # evaluate
        y_true, y_prob, paths = evaluate(model, val_loader)
        metrics = binary_metrics(y_true, y_prob)
        dt = time.time() - t0
        print(f"Epoch {epoch+1}/{EPOCHS} | time={dt:.1f}s | train_loss={train_loss:.4f} | val_acc={metrics['acc']:.4f} | val_f1={metrics['f1']:.4f} | val_auc={metrics['auc']:.4f}")

        # save predictions
        pred_df = pd.DataFrame({"path": paths, "label": y_true, "pred_prob": y_prob})
        pred_df.to_csv("val_predictions_epoch_{:02d}.csv".format(epoch+1), index=False)

        # save best
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            torch.save({"model_state": model.state_dict(),
                        "optimizer_state": optimizer.state_dict(),
                        "epoch": epoch,
                        "best_f1": best_f1},
                       SAVE_BEST)
            print(f"  >> Saved best model (f1={best_f1:.4f}) -> {SAVE_BEST}")

    print("Training complete. Best val F1:", best_f1)

if __name__ == "__main__":
    main()
