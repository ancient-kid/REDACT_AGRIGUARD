# nodes/image_input.py
import os

def run(inputs: dict):
    """Validate that the provided image path exists and preserve incoming state."""
    image_path = inputs.get("image_path")
    if not image_path:
        raise ValueError("image_path required")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")

    state = dict(inputs)
    state["image_path"] = image_path
    return state
