# train_disease_torch_fixed_amp.py
"""
Multi-class disease classification training script
- Same style as train_torch_fixed_amp.py
- Uses SimpleCNN but with multi-class output
- Expects folder layout:
    data/
      train/
        Class1/
        Class2/
        ...
      valid/
        Class1/
        Class2/
        ...
Each folder name is treated as a separate disease class.
"""

import os
import time
import random
from pathlib import Path
from typing import Tuple, List, Dict

import numpy as np
import pandas as pd
from PIL import Image

import torch
from torch import nn, optim
from torch import amp
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import torchvision.transforms as T

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

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
SAVE_BEST = Path("best_disease_model.pth")
DEBUG = False        # set True for fast iteration
DEBUG_N = 8000       # number of samples if DEBUG=True
PRINT_EVERY = 100    # steps

# If True, ignore classes whose folder name contains "healthy"
EXCLUDE_HEALTHY = True

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
# Dataset: multi-class (each folder = 1 class)
# ----------------------------
class MultiClassFolderDataset(Dataset):
    def __init__(self, root_dir: Path, img_size=IMG_SIZE, train=True):
        self.root_dir = Path(root_dir)
        if not self.root_dir.exists():
            raise FileNotFoundError(f"{root_dir} not found")

        # discover class folders
        class_names = sorted([d.name for d in self.root_dir.iterdir() if d.is_dir()])
        if EXCLUDE_HEALTHY:
            class_names = [c for c in class_names if "healthy" not in c.lower()]

        if len(class_names) < 2:
            raise ValueError(f"Need at least 2 classes, found: {class_names}")

        self.class_names = class_names
        self.class_to_idx = {c: i for i, c in enumerate(self.class_names)}
        self.idx_to_class = {i: c for c, i in self.class_to_idx.items()}

        self.items = []
        for cls_name in self.class_names:
            cls_dir = self.root_dir / cls_name
            for f in cls_dir.iterdir():
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    self.items.append((str(f), self.class_to_idx[cls_name]))

        if train:
            self.transform = T.Compose([
                T.Resize((img_size, img_size)),
                T.RandomHorizontalFlip(),
                T.RandomRotation(8),
                T.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
                T.ToTensor(),
                T.Normalize([0.485, 0.456, 0.406],
                            [0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = T.Compose([
                T.Resize((img_size, img_size)),
                T.ToTensor(),
                T.Normalize([0.485, 0.456, 0.406],
                            [0.229, 0.224, 0.225]),
            ])

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        path, label = self.items[idx]
        img = Image.open(path).convert("RGB")
        img = self.transform(img)
        return img, torch.tensor(label, dtype=torch.long), path

# ----------------------------
# Simple CNN (multi-class head)
# ----------------------------
class SimpleCNNMulti(nn.Module):
    def __init__(self, num_classes: int):
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
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x).view(x.size(0), -1)
        x = self.classifier(x)
        return x  # logits (B, num_classes)

# ----------------------------
# Build datasets + loaders
# ----------------------------
def build_loaders(train_dir, val_dir, batch_size=BATCH_SIZE, debug=DEBUG):
    train_ds = MultiClassFolderDataset(train_dir, train=True)
    val_ds = MultiClassFolderDataset(val_dir, train=False)

    if debug:
        train_ds.items = random.sample(train_ds.items, min(DEBUG_N, len(train_ds.items)))
        val_ds.items = random.sample(val_ds.items, min(2048, len(val_ds.items)))
        print(f"[DEBUG] train samples: {len(train_ds)}, val samples: {len(val_ds)}")

    # class counts and sampler
    labels = [lbl for _, lbl in train_ds.items]
    num_classes = len(train_ds.class_names)
    counts = {i: 0 for i in range(num_classes)}
    for x in labels:
        counts[int(x)] += 1
    print("Train class counts (by index):", counts)

    weights = []
    for lbl in labels:
        weights.append(1.0 / (counts[int(lbl)] + 1e-9))
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler,
                              num_workers=NUM_WORKERS, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=NUM_WORKERS, pin_memory=True)

    metadata = {
        "n_train": len(train_ds),
        "n_val": len(val_ds),
        "class_names": train_ds.class_names,
        "class_to_idx": train_ds.class_to_idx,
    }
    return train_loader, val_loader, metadata

# ----------------------------
# Metrics helpers (multi-class)
# ----------------------------
def multiclass_metrics(y_true: np.ndarray, y_pred: np.ndarray):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    return {"acc": acc, "prec": prec, "rec": rec, "f1": f1, "cm": cm}

# ----------------------------
# Train / Eval loops with amp
# ----------------------------
def train_one_epoch(model, loader, optimizer, criterion, scaler, epoch_idx, total_epochs):
    model.train()
    running_loss = 0.0
    n = 0
    use_amp = (DEVICE.type == "cuda")
    for batch_idx, (imgs, labels, _) in enumerate(loader):
        imgs = imgs.to(DEVICE, non_blocking=True)
        labels = labels.to(DEVICE, non_blocking=True)  # (B,)

        optimizer.zero_grad()
        with amp.autocast("cuda", enabled=use_amp):
            logits = model(imgs)        # (B, num_classes)
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

def evaluate(model, loader, class_names: List[str]):
    model.eval()
    use_amp = (DEVICE.type == "cuda")

    all_logits = []
    all_labels = []
    all_paths = []

    with torch.no_grad():
        for imgs, labels, paths in loader:
            imgs = imgs.to(DEVICE, non_blocking=True)
            labels_np = labels.numpy()
            with amp.autocast("cuda", enabled=use_amp):
                logits = model(imgs)

            all_logits.append(logits.cpu())
            all_labels.append(labels_np)
            all_paths.extend(paths)

    if not all_logits:
        return None, None

    logits_all = torch.cat(all_logits, dim=0)          # (N, C)
    labels_all = np.concatenate(all_labels)            # (N,)
    probs_all = F.softmax(logits_all, dim=1).numpy()   # (N, C)
    preds_all = probs_all.argmax(axis=1)               # (N,)

    metrics = multiclass_metrics(labels_all, preds_all)

    # Build dataframe of predictions
    idx_to_class = {i: c for i, c in enumerate(class_names)}
    true_labels_str = [idx_to_class[i] for i in labels_all]
    pred_labels_str = [idx_to_class[i] for i in preds_all]
    max_conf = probs_all.max(axis=1)

    pred_df = pd.DataFrame({
        "path": all_paths,
        "true_label": true_labels_str,
        "pred_label": pred_labels_str,
        "pred_conf": max_conf,
    })

    return metrics, pred_df

# ----------------------------
# Main
# ----------------------------
def main():
    train_loader, val_loader, meta = build_loaders(TRAIN_DIR, VAL_DIR, batch_size=BATCH_SIZE, debug=DEBUG)
    class_names = meta["class_names"]
    print("Classes:", class_names)

    model = SimpleCNNMulti(num_classes=len(class_names)).to(DEVICE)
    print(model)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    scaler = amp.GradScaler(device="cuda" if DEVICE.type == "cuda" else "cpu") if DEVICE.type == "cuda" else None

    best_f1 = -1.0
    for epoch in range(EPOCHS):
        t0 = time.time()
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, scaler, epoch, EPOCHS)
        scheduler.step()

        metrics, pred_df = evaluate(model, val_loader, class_names)
        if metrics is None:
            print("No validation data!")
            break

        dt = time.time() - t0
        print(f"Epoch {epoch+1}/{EPOCHS} | time={dt:.1f}s | "
              f"train_loss={train_loss:.4f} | "
              f"val_acc={metrics['acc']:.4f} | val_f1_macro={metrics['f1']:.4f}")

        # Save predictions CSV per epoch
        pred_df.to_csv(f"val_disease_predictions_epoch_{epoch+1:02d}.csv", index=False)

        # Save best by macro F1
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            torch.save({
                "model_state": model.state_dict(),
                "class_names": class_names,
                "class_to_idx": meta["class_to_idx"],
                "epoch": epoch,
                "best_f1_macro": best_f1,
            }, SAVE_BEST)
            print(f"  >> Saved best disease model (macro F1={best_f1:.4f}) -> {SAVE_BEST}")

    print("Training complete. Best val macro F1:", best_f1)

if __name__ == "__main__":
    main()

