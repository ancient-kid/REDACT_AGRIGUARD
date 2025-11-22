# nodes/shap_explain.py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np
import torch
# TensorFlow can be optional here, fallback if not available
try:
    import tensorflow as tf
except ImportError:  # pragma: no cover - TF already required by preprocess but keep safe
    tf = None
import shap
from PIL import Image
from pathlib import Path

from .evaluate import SimpleCNN, DEVICE  # fixed import


# Where to store outputs
OUT_DIR = Path(__file__).resolve().parent / "shap_explanations"
OUT_DIR.mkdir(parents=True, exist_ok=True)


MODEL_PATH = Path(__file__).resolve().parents[2] / "best_model.pth"
_MODEL = None
# ...existing code...


def _load_model():
    global _MODEL
    if _MODEL is None:

        model = SimpleCNN().to(DEVICE)
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
        model.load_state_dict(checkpoint["model_state"])
        model.eval()
        _MODEL = model
    return _MODEL


def _to_torch_tensor(img):
    if isinstance(img, torch.Tensor):
        tensor = img
    elif isinstance(img, np.ndarray):
        tensor = torch.from_numpy(img)
    elif tf is not None and isinstance(img, tf.Tensor):
        tensor = torch.from_numpy(img.numpy())
    elif hasattr(img, "numpy"):
        tensor = torch.from_numpy(img.numpy())
    else:
        raise TypeError("Unsupported tensor type for SHAP")
    if tensor.dim() == 3:
        tensor = tensor.unsqueeze(0)
    return tensor

def run(inputs: dict):
    state = dict(inputs)
    model = _load_model()
    device = next(model.parameters()).device
    raw_tensor = inputs["image_tensor"]

    image_tensor = _to_torch_tensor(raw_tensor).float()

    # convert NHWC -> NCHW when needed
    if image_tensor.dim() == 4 and image_tensor.shape[-1] == 3:
        image_tensor = image_tensor.permute(0, 3, 1, 2)
    elif image_tensor.dim() == 3 and image_tensor.shape[-1] == 3:
        image_tensor = image_tensor.permute(2, 0, 1).unsqueeze(0)

    image_tensor = image_tensor.to(device)  # assume this is torch.Tensor or convert accordingly

    # If image_tensor is a tf.Tensor / numpy array, convert to torch
    if isinstance(image_tensor, np.ndarray):
        image_tensor = torch.from_numpy(image_tensor).to(next(model.parameters()).device)
    if image_tensor.dim() == 4 and image_tensor.shape[0] == 1:
        pass
    else:
        image_tensor = image_tensor.unsqueeze(0)

    # Move to correct device, ensure float
    image_tensor = image_tensor.float().to(next(model.parameters()).device)

    # Use SHAP with PyTorch model — e.g., KernelExplainer or GradientExplainer if supported
    try:
        explainer = shap.GradientExplainer(model, image_tensor)
        shap_values = explainer.shap_values(image_tensor)
    except Exception as e:
        # fallback
        with torch.no_grad():
            logits = model(image_tensor)
            pred_index = torch.argmax(logits, dim=1).item()
        image_tensor.requires_grad_(True)
        scores = model(image_tensor)[0, pred_index]
        scores.backward()
        grads = image_tensor.grad[0].cpu().numpy()
        grad_abs = np.abs(grads).mean(axis=0)
        sal = (grad_abs - grad_abs.min()) / (grad_abs.max() - grad_abs.min() + 1e-8)
        heatmap = (sal * 255).astype('uint8')
        heatpath = OUT_DIR / f"saliency_heatmap_{Path(inputs.get('image_path', 'img')).name}.png"
        Image.fromarray(heatmap).resize((224, 224)).save(heatpath)
        state["shap_path"] = str(heatpath)
        state["shap_method"] = "gradients"
        state["shap_note"] = str(e)
        state.pop("image_tensor", None)
        return state

    # If shap_values is list etc handle like before
    pred_label = inputs.get("pred_label")
    if pred_label is None:
        with torch.no_grad():
            logits = model(image_tensor)
            pred_label = int(torch.argmax(logits, dim=1).item())

    # Assume shap_values is list of arrays
    sv = shap_values[pred_label][0] if isinstance(shap_values, list) else shap_values[0][0]
    heat = np.mean(np.abs(sv), axis=0)  # adjust axes depending on shape
    heat = (heat - heat.min()) / (heat.max() - heat.min() + 1e-8)
    heat_rgb = (heat * 255).astype('uint8')
    heatpath = OUT_DIR / f"shap_heatmap_{Path(inputs.get('image_path','img')).name}.png"
    plt.figure(figsize=(4, 4))
    plt.axis('off')
    plt.imshow(heat, cmap='jet')
    plt.savefig(heatpath, bbox_inches='tight', pad_inches=0)
    plt.close()

    state["shap_path"] = str(heatpath)
    state["shap_method"] = "shap_gradient"
    state.pop("image_tensor", None)
    return state