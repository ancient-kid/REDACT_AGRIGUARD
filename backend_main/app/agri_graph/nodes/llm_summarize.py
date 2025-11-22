# nodes/llm_summarize.py

import os
import json
from dotenv import load_dotenv
load_dotenv()

# Use the new Google GenAI SDK
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY missing in environment variables")

client = genai.Client(api_key=api_key)

def run(inputs: dict):
    state = dict(inputs)  # keep fields like image_path
    pred_class = state.get("pred_class", "")
    prob_h = state.get("prob_healthy", 0.0)
    prob_d = state.get("prob_diseased", 0.0)
    shap_path = state.get("shap_path", "")
    recs = state.get("recommendations", [])
    disease_details = state.get("disease_details", {})
    disease_name = disease_details.get("predicted_disease", state.get("disease_name", "Unknown"))
    disease_conf = disease_details.get("confidence", 0.0)
    severity = state.get("severity", "Unknown")
    image_path = state.get("image_path", "image")

    prompt = f"""
    You are an agricultural assistant. Analyze the following detection:
    - Image: {image_path}
    - Prediction: {pred_class}
    - Confidence: healthy={prob_h:.3f}, diseased={prob_d:.3f}
    - Severity: {severity}
    - Recommendations: {json.dumps(recs)}
    - SHAP heatmap file path: {shap_path}
    -   Disease identification: {disease_name} ({disease_conf:.3f} confidence)
    - Top disease candidates: {json.dumps(disease_details.get("top_classes", []))}

    Write a short farmer-friendly summary (3-5 lines) that:
    1) States whether the plant is healthy or diseased
    2) Gives a clear action (isolate, inspect, apply organic neem, or monitor)
    3) Mentions confidence and where the SHAP heatmap highlights (e.g., "spots near leaf edges")
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    state["summary"] = response.text
    state["prompt"] = prompt
    return state
