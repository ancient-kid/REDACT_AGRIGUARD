# infer_single_image.py

import argparse
from pathlib import Path

import torch
from PIL import Image
import torchvision.transforms as T

from backend_main.app.agri_graph.nodes.evaluate  import SimpleCNN, DEVICE, IMG_SIZE

MODEL_PATH = "best_model.pth"

# Same normalization as validation
transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225]),
])

def load_model(model_path: str = MODEL_PATH):
    model = SimpleCNN().to(DEVICE)
    checkpoint = torch.load(model_path, map_location=DEVICE)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model

def predict_image(model, image_path: str, thresh: float = 0.5):
    img = Image.open(image_path).convert("RGB")
    x = transform(img).unsqueeze(0).to(DEVICE)  # (1,3,H,W)

    with torch.no_grad():
        logits = model(x)
        prob_healthy = torch.sigmoid(logits).item()  # scalar

    # Your labels: healthy=1, diseased=0
    if prob_healthy >= thresh:
        cls = "HEALTHY"
        confidence = prob_healthy
    else:
        cls = "DISEASED"
        confidence = 1.0 - prob_healthy  # confidence for diseased

    return cls, confidence, prob_healthy

def main():
    parser = argparse.ArgumentParser(description="Infer single leaf image (Healthy vs Diseased)")
    parser.add_argument("--image", "-i", type=str, required=True, help="Path to input image")
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path}")

    print(f"Loading model from: {MODEL_PATH}")
    model = load_model(MODEL_PATH)

    cls, conf, prob_healthy = predict_image(model, str(img_path))

    print("\n========== PREDICTION RESULT ==========")
    print(f"Image       : {img_path}")
    print(f"Prediction  : {cls}")
    print(f"Confidence  : {conf*100:.2f}%")
    print(f"P(Healthy)  : {prob_healthy*100:.2f}%")
    print("=======================================")

if __name__ == "__main__":
    main()
