import argparse
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from torch.utils.data import DataLoader

from app.multi_class_cnn_trainer import (
    DEVICE,
    IMG_SIZE,
    MultiClassFolderDataset,
    SimpleCNNMulti,
    VAL_DIR as MULTI_VAL_DIR,
)
from app.binary_cnn_trainer import (
    DEVICE as DEVICE_BIN,
    IMG_SIZE as IMG_SIZE_BIN,
    BinaryFolderDataset,
    BinarySimpleCNN,
    VAL_DIR as BINARY_VAL_DIR,
)


def evaluate(model, loader, class_names):
    model.eval()
    preds, targets = [], []
    with torch.no_grad():
        for images, labels, *_ in loader:
            images = images.to(DEVICE)
            logits = model(images)
            preds.extend(torch.argmax(logits, dim=1).cpu().tolist())
            targets.extend(labels.tolist())
    acc = accuracy_score(targets, preds)
    f1 = f1_score(targets, preds, average="macro")
    cm = confusion_matrix(targets, preds)
    return acc, f1, cm


def build_loader(dataset_class, val_dir, img_size, batch_size=32, train=False):
    dataset = dataset_class(val_dir, img_size=img_size, train=train)
    return DataLoader(dataset, batch_size=batch_size, shuffle=False)


def load_checkpoint(path: Path, model_class, num_classes):
    checkpoint = torch.load(path, map_location=DEVICE)
    model = model_class(num_classes=num_classes).to(DEVICE)
    model.load_state_dict(checkpoint["model_state"] if "model_state" in checkpoint else checkpoint)
    model.eval()
    return model


def run_multi_model(model_path: Path):
    loader = build_loader(MultiClassFolderDataset, MULTI_VAL_DIR, IMG_SIZE)
    class_names = loader.dataset.class_names
    model = load_checkpoint(model_path, SimpleCNNMulti, len(class_names))
    acc, f1, cm = evaluate(model, loader, class_names)
    return "multi-class", model_path.name, acc, f1, cm, class_names


def run_binary_model(model_path: Path):
    loader = build_loader(BinaryLeafDataset, BINARY_VAL_DIR, IMG_SIZE_BIN)
    class_names = loader.dataset.class_names
    model = load_checkpoint(model_path, BinarySimpleCNN, len(class_names))
    acc, f1, cm = evaluate(model, loader, class_names)
    return "binary", model_path.name, acc, f1, cm, class_names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", required=True, help="Paths to .pth files")
    args = parser.parse_args()

    for pth in args.models:
        path = Path(pth)
        if "multi" in path.name.lower():
            kind, name, acc, f1, cm, classes = run_multi_model(path)
        else:
            kind, name, acc, f1, cm, classes = run_binary_model(path)

        print(f"\n[{kind.upper()}] {name}")
        print(f"  Accuracy : {acc:.4f}")
        print(f"  Macro F1 : {f1:.4f}")
        print(f"  Classes  : {classes}")
        print("  Confusion Matrix:")
        print(cm)


if __name__ == "__main__":
    main()