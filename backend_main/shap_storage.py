from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
SHAP_GRADIENT_DIR = BASE_DIR / "data" / "shap_gradients"
SHAP_GRADIENT_DIR.mkdir(parents=True, exist_ok=True)


def store_shap_gradient(upload_id: str, shap_image_path: Optional[str], context: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Copy the SHAP heatmap into a dedicated development folder and record metadata."""
    if not shap_image_path:
        return None

    source = Path(shap_image_path)
    if not source.exists():
        return None

    destination = SHAP_GRADIENT_DIR / f"{upload_id}_shap_gradient.png"
    shutil.copyfile(source, destination)

    metadata = {
        "upload_id": upload_id,
        "pred_class": context.get("pred_class") if context else None,
        "shap_method": context.get("shap_method") if context else None,
        "stored_at": datetime.utcnow().isoformat() + "Z",
        "source_path": str(source),
    }

    metadata_path = SHAP_GRADIENT_DIR / f"{upload_id}_metadata.json"
    metadata_path.write_text(json.dumps({k: v for k, v in metadata.items() if v is not None}, indent=2))

    return str(destination)
