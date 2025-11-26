import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from torch.utils.data import DataLoader

from .multi_class_cnn_trainer import (
    DEVICE,
    IMG_SIZE,
    MultiClassFolderDataset,
    SAVE_BEST,
    SimpleCNNMulti,
)


def load_model(model_path: Path | str):
    ckpt = torch.load(model_path, map_location=DEVICE)
    class_names = ckpt.get("class_names")
    if not class_names:
        raise ValueError("Checkpoint is missing class names")

    model = SimpleCNNMulti(num_classes=len(class_names)).to(DEVICE)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model, class_names


def build_loader(val_dir: Path, batch_size: int):
    dataset = MultiClassFolderDataset(val_dir, img_size=IMG_SIZE, train=False)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    return loader, dataset.class_names


def predict(model: torch.nn.Module, loader: DataLoader):
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for imgs, labels, _ in loader:
            imgs = imgs.to(DEVICE)
            logits = model(imgs)
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.append(preds)
            all_targets.append(labels.numpy())

    return np.concatenate(all_targets), np.concatenate(all_preds)


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str],
    output_path: Path,
    title: str = "Confusion Matrix",
):
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    fig, ax = plt.subplots(figsize=(min(12, len(class_names) * 0.7), 10))
    disp.plot(ax=ax, values_format="d", cmap="Blues", colorbar=False)
    ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_matrix_csv(cm: np.ndarray, class_names: list[str], csv_path: Path):
    header = "," + ",".join(class_names)
    rows = []
    for label, row in zip(class_names, cm):
        row_str = ",".join(str(int(x)) for x in row)
        rows.append(f"{label},{row_str}")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("\n".join([header] + rows))


def main():
    parser = argparse.ArgumentParser(description="Evaluate confusion matrix from validation set")
    parser.add_argument(
        "--val-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "valid",
        help="Path to validation data folders",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "best_disease_model.pth",
        help="Path to saved PyTorch model",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "results" / "confusion_matrix.png",
        help="PNG path for the confusion matrix heatmap",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Optional CSV path to dump raw matrix",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for validation loader",
    )

    args = parser.parse_args()

    model_path = args.model
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")

    loader, class_names = build_loader(args.val_dir, batch_size=args.batch_size)
    model, class_names = load_model(model_path)

    y_true, y_pred = predict(model, loader)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))

    print("Confusion matrix (rows=true, cols=predicted):")
    print(cm)

    plot_confusion_matrix(cm, class_names, args.output)
    print(f"Saved confusion matrix figure to {args.output}")

    if args.csv:
        save_matrix_csv(cm, class_names, args.csv)
        print(f"Saved confusion matrix CSV to {args.csv}")


if __name__ == "__main__":
    main()
