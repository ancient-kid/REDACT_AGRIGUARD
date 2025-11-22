import hashlib
from PIL import Image
import numpy as np
import cv2
import os
from skimage.measure import shannon_entropy


# ===============================================================
# BASIC SECURITY
# ===============================================================

def generate_sha256_hash(image_bytes):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(image_bytes)
    return sha256_hash.hexdigest()


# ===============================================================
# VISUAL CORRUPTION DETECTORS
# ===============================================================

def detect_color_banding(path, threshold=40):
    try:
        img = cv2.imread(path)
        if img is None:
            return True
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        row_means = np.mean(gray, axis=1)
        diffs = np.abs(np.diff(row_means))
        return np.max(diffs) > threshold
    except:
        return True


def detect_low_entropy(path, threshold=3.0):
    try:
        img = Image.open(path).convert("L")
        ent = shannon_entropy(np.array(img))
        return ent < threshold
    except:
        return True


def detect_unusual_color_distribution(path, threshold=5):
    try:
        img = cv2.imread(path)
        if img is None:
            return True

        b, g, r = cv2.split(img)
        for ch in [b, g, r]:
            if np.var(ch) < threshold:
                return True
        return False
    except:
        return True


def detect_extreme_blur(path, threshold=10):
    try:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        return cv2.Laplacian(img, cv2.CV_64F).var() < threshold
    except:
        return True


def jpeg_decode_valid(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return img is not None
    except:
        return False


# ===============================================================
# FORMAT VALIDATION USING PIL
# ===============================================================

def validate_image_format(image_file):
    try:
        img = Image.open(image_file)
        img.verify()

        image_file.seek(0)
        img = Image.open(image_file)
        img.load()

        if img.mode not in ['RGB', 'RGBA', 'L']:
            img_test = img.convert("RGB")
        else:
            img_test = img

        pixels = list(img_test.getdata())
        if len(pixels) == 0:
            return False, "No pixel data", None

        for px in pixels[:100]:
            if isinstance(px, tuple):
                if any([c < 0 or c > 255 for c in px]):
                    return False, "Pixel out of range", None

        extrema = img.getextrema()

        return True, {
            'format': img.format,
            'mode': img.mode,
            'width': img.width,
            'height': img.height
        }, img

    except Exception as e:
        return False, str(e), None


# ===============================================================
# MAIN VALIDATOR
# ===============================================================

def check_image_corruption(uploaded_file, temp_path="temp/temp_image"):
    if not os.path.exists("temp"):
        os.mkdir("temp")

    with open(temp_path, "wb") as f:
        f.write(uploaded_file)

    results = {
        "hash": generate_sha256_hash(uploaded_file),
        "format_valid": False,
        "not_empty": False,
        "not_corrupted": False,
        "visual_corruption": False,
        "format_info": {},
        "errors": [],
        "warnings": []
    }

    if len(uploaded_file) == 0:
        results["errors"].append("File empty")
        return results

    results["not_empty"] = True

    # Format check
    from io import BytesIO
    buf = BytesIO(uploaded_file)
    is_valid, info, img = validate_image_format(buf)

    if not is_valid:
        results["errors"].append(f"Image format error: {info}")
    else:
        results["format_valid"] = True
        results["format_info"] = info
        results["not_corrupted"] = True

    # Visual Corruption Tests
    if detect_color_banding(temp_path):
        results["visual_corruption"] = True
        results["errors"].append("Color banding detected")

    if detect_low_entropy(temp_path):
        results["visual_corruption"] = True
        results["errors"].append("Low entropy (glitch-like)")

    if detect_unusual_color_distribution(temp_path):
        results["visual_corruption"] = True
        results["errors"].append("Unnatural color distribution")

    if detect_extreme_blur(temp_path):
        results["warnings"].append("Image extremely blurred")

    if not jpeg_decode_valid(temp_path):
        results["visual_corruption"] = True
        results["errors"].append("JPEG decode failure")

    if results["visual_corruption"]:
        results["not_corrupted"] = False

    return results
