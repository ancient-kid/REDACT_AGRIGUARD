import logging
from pathlib import Path

import torch
from PIL import Image
import torchvision.transforms as T

from .agri_graph.nodes.evaluate import SimpleCNN, DEVICE, IMG_SIZE
# SimpleCNN is imported from the same file that defines the architecture used for training

LOGGER = logging.getLogger(__name__)

# Load the exact checkpoint produced by train_torch_fixed_amp.py
import os
from pathlib import Path

# Get the correct base directory
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = os.path.join(BASE_DIR, "best_model.pth")

# Same normalization as validation set
transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225]),
])

model = None
CLASS_NAMES = ["DISEASED", "HEALTHY"]  
# index 0 → diseased, index 1 → healthy


def load_model():
    """
    Load the trained SimpleCNN binary classifier with 1 logit output.
    """
    global model

    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)

    model = SimpleCNN().to(DEVICE)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    LOGGER.info("Loaded model from %s", MODEL_PATH)
    LOGGER.info("Binary classes: %s", CLASS_NAMES)


load_model()


def run_prediction(image_path):
    """
    Run binary disease prediction using the trained CNN.
    Returns:
        predicted_class (str),
        confidence_of_predicted_class (float),
        prob_diseased (float),
        prob_healthy (float)
    """
    print(f"[run_prediction] image_path={image_path}")

    img = Image.open(image_path).convert("RGB")
    x = transform(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(x)  # shape (1,1)
        prob_diseased = torch.sigmoid(logits).item()   # probability of class 1
        prob_healthy = 1.0 - prob_diseased            # probability of class 0

    # predicted class (threshold = 0.5)
    pred_idx = 1 if prob_diseased >= 0.5 else 0
    pred_class = CLASS_NAMES[pred_idx]
    confidence = prob_diseased if pred_idx == 1 else prob_healthy

    print(
        f"[run_prediction] class={pred_class} "
        f"conf={confidence:.4f} "
        f"healthy={prob_healthy:.4f} "
        f"diseased={prob_diseased:.4f}"
    )

    return pred_class, confidence, prob_diseased, prob_healthy
