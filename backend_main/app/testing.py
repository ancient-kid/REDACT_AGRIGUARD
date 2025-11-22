import torch
import numpy as np
from PIL import Image, ImageDraw
import torchvision.transforms as T
from pathlib import Path
import cv2

from multi_class_cnn import SimpleCNNMulti, SAVE_BEST, DEVICE, IMG_SIZE

# ------------------------
# SAME NORMALIZATION
# ------------------------
transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225]),
])

# ================================================================
#                       GRAD-CAM
# ================================================================
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.features = None

        target_layer.register_forward_hook(self.save_features)
        target_layer.register_backward_hook(self.save_gradients)

    def save_features(self, m, i, o):
        self.features = o

    def save_gradients(self, m, gi, go):
        self.gradients = go[0]

    def __call__(self, x, class_idx):
        out = self.model(x)
        self.model.zero_grad()

        one_hot = torch.zeros_like(out)
        one_hot[0][class_idx] = 1
        out.backward(gradient=one_hot)

        weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)
        cam = torch.sum(weights * self.features, dim=1).squeeze()

        cam = torch.relu(cam).detach().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

        return cam


# ================================================================
#                 LOAD MODEL + CLASSES
# ================================================================
def load_model_and_classes():
    ckpt = torch.load(SAVE_BEST, map_location=DEVICE)
    model = SimpleCNNMulti(num_classes=len(ckpt["class_names"]))
    model.load_state_dict(ckpt["model_state"])
    model.to(DEVICE)
    model.eval()
    return model, ckpt["class_names"], ckpt["class_to_idx"]


# ================================================================
#          BBOX DIRECTLY FROM CAM (NO MASK AT ALL)
# ================================================================
def get_bbox_from_cam(cam):
    """
    Top-K hotspot extraction (never covers whole image).
    Focuses only on the strongest disease region.
    """

    H, W = cam.shape

    cam_norm = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

    # --- Top 5% hottest pixels only ---
    k = 0.95  # keep top 5%
    thr = np.quantile(cam_norm, k)

    binary = (cam_norm >= thr).astype(np.uint8)

    # Slight dilation to form a connected region
    kernel = np.ones((15, 15), np.uint8)
    binary = cv2.dilate(binary, kernel, iterations=2)

    cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not cnts:
        return None

    c = max(cnts, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)

    # Padding for visual clarity
    pad = 0.2
    pw, ph = int(w * pad), int(h * pad)

    x1 = max(0, x - pw)
    y1 = max(0, y - ph)
    x2 = min(W, x + w + pw)
    y2 = min(H, y + h + ph)

    return x1, y1, x2, y2




    



# ================================================================
#               DRAW BBOX ON ORIGINAL IMAGE
# ================================================================
def draw_bbox_on_image(orig_img, cam, out_path):
    cam_up = cv2.resize(cam, (orig_img.width, orig_img.height))
    bbox = get_bbox_from_cam(cam_up)

    img = orig_img.copy()
    draw = ImageDraw.Draw(img)

    if bbox is None:
        print("⚠ No bbox found — saving image without bbox")
        img.save(out_path)
        return

    x1, y1, x2, y2 = bbox
    draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0), width=10)
    img.save(out_path)
    print("✔ BBox drawn:", bbox)


# ================================================================
#               GRADCAM OVERLAY
# ================================================================
def overlay_gradcam_on_image(orig_img, cam, out_path):
    cam_r = cv2.resize(cam, (orig_img.width, orig_img.height))
    heat = cv2.applyColorMap((cam_r * 255).astype(np.uint8), cv2.COLORMAP_JET)
    heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    blended = cv2.addWeighted(np.array(orig_img), 0.55, heat, 0.45, 0)
    Image.fromarray(blended).save(out_path)


# ================================================================
#                           MAIN
# ================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", "-i", required=True)
    parser.add_argument("--out", "-o", default="./gradcam_outputs")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)

    model, class_names, class_to_idx = load_model_and_classes()

    orig = Image.open(args.image).convert("RGB")
    img_tensor = transform(orig).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        out = model(img_tensor)
        probs = torch.softmax(out, dim=1)
        cls_idx = torch.argmax(probs).item()
        cls = class_names[cls_idx]
        conf = probs[0][cls_idx].item()

    print(f"📌 Pred: {cls}  —  conf={conf:.3f}")

    target_layer = model.features[-2]
    cam = GradCAM(model, target_layer)(img_tensor, cls_idx)

    overlay_gradcam_on_image(orig, cam, out_dir / "overlay.png")
    draw_bbox_on_image(orig, cam, out_dir / "bbox.png")

    print("✔ Saved:", out_dir)


if __name__ == "__main__":
    main()
