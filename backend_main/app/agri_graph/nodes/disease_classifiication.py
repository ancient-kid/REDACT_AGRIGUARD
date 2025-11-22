import torch
import torch.nn.functional as F
import torchvision.transforms as T
from pathlib import Path
from PIL import Image

from .multi_class_cnn import SimpleCNNMulti, DEVICE, IMG_SIZE

DISEASE_MODEL_PATH = Path(__file__).resolve().parents[3] / "best_disease_model.pth"
_transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225]),
])

_disease_model = None
_class_names = None

def _load_disease_model():
    global _disease_model, _class_names
    if _disease_model is None:
        ckpt = torch.load(DISEASE_MODEL_PATH, map_location=DEVICE)
        _class_names = ckpt["class_names"]
        _disease_model = SimpleCNNMulti(num_classes=len(_class_names)).to(DEVICE)
        _disease_model.load_state_dict(ckpt["model_state"])
        _disease_model.eval()
    return _disease_model, _class_names

def run(inputs: dict):
    state = dict(inputs)
    pred_class = (state.get("pred_class") or "").lower()
    image_path = state.get("image_path")

    if pred_class == "healthy" or image_path is None:
        state.setdefault("disease_details", {
            "predicted_disease": "None",
            "confidence": 0.0,
            "top_classes": []
        })
        return state

    model, class_names = _load_disease_model()
    img = Image.open(image_path).convert("RGB")
    x = _transform(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(x)
        probs = F.softmax(logits, dim=1).cpu().numpy().ravel()

    top_indices = probs.argsort()[::-1][:3]
    top = [
        {"label": class_names[i], "probability": float(probs[i])}
        for i in top_indices
    ]

    state["disease_name"] = top[0]["label"]
    state["disease_details"] = {
        "predicted_disease": top[0]["label"],
        "confidence": top[0]["probability"],
        "top_classes": top
    }
    return state