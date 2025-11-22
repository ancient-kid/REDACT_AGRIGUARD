# nodes/report_output.py
import json
import os
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[2] / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run(inputs: dict):
    state = dict(inputs)

    report = {
        "image_path": state.get("image_path"),
        "prediction": state.get("pred_class"),
        "prob_healthy": state.get("prob_healthy"),
        "prob_diseased": state.get("prob_diseased"),
        "severity": state.get("severity"),
        "recommendations": state.get("recommendations"),
        "shap_heatmap": state.get("shap_path"),
        "summary": state.get("summary"),
    }

    base_name = os.path.basename(report["image_path"]) if report.get("image_path") else "unknown_image"
    out_path = OUT_DIR / f"report_{base_name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    state["report_path"] = str(out_path)
    state["report"] = report
    return state
