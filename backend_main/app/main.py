# backend_main/app/main.py

import sys
import os
import base64
from pathlib import Path
import shutil

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .validators import check_image_corruption

# Add project root and nodes folder to path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = PROJECT_ROOT / "agri_graph" / "nodes"
sys.path.append(str(NODES_PATH))

load_dotenv()

# Import LangGraph classes
from langgraph.graph import StateGraph, START, END

# Import your node functions
from .agri_graph.nodes.image_input import run as image_input
from .agri_graph.nodes.llm_summarize import run as llm_summarize
from .agri_graph.nodes.preprocess import run as preprocess
from .agri_graph.nodes.model_predict import model_predict as model_predict
from .agri_graph.nodes.shap_explain import run as shap_explain
from .agri_graph.nodes.recommender import run as recommender
from .agri_graph.nodes.report_output import run as report_output
from .agri_graph.nodes.disease_classifiication import run as disease_classification


# Build the Graph
state_schema = dict  # for now using simple dict schema
builder = StateGraph(state_schema)

builder.add_node("ImageInput", image_input)
builder.add_node("Preprocess", preprocess)
builder.add_node("ModelPredict", model_predict)
builder.add_node("DiseaseClassifier", disease_classification)
builder.add_node("SHAPExplain", shap_explain)
builder.add_node("RuleRecommender", recommender)
builder.add_node("LLMSummarize", llm_summarize)
builder.add_node("ReportOutput", report_output)

# Define flow edges (per your YAML)
# ...existing code...
builder.add_edge(START, "ImageInput")
builder.add_edge("ImageInput", "Preprocess")
builder.add_edge("Preprocess", "ModelPredict")
builder.add_edge("ModelPredict", "DiseaseClassifier")
builder.add_edge("DiseaseClassifier", "SHAPExplain")
builder.add_edge("SHAPExplain", "RuleRecommender")
builder.add_edge("RuleRecommender", "LLMSummarize")
builder.add_edge("LLMSummarize", "ReportOutput")
builder.add_edge("ReportOutput", END)

# Compile graph
compiled_graph = builder.compile()

# Create FastAPI app
app = FastAPI(title="AgriGuard Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "service": "agri-guard-backend"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # Save uploaded image temporarily
    tmp_path = PROJECT_ROOT / "temp_upload.jpg"
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run graph pipeline
    initial_state = {
        "image_path": str(tmp_path),
        "original_filename": file.filename,
    }
    result_state = compiled_graph.invoke(initial_state)

    shap_base64 = None
    shap_path = result_state.get("shap_path")
    if shap_path and Path(shap_path).exists():
        with open(shap_path, "rb") as shp:
            shap_base64 = base64.b64encode(shp.read()).decode("utf-8")

    # Cleanup
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    payload = {
        "image_path": result_state.get("image_path"),
        "pred_class": result_state.get("pred_class"),
        "prob_healthy": result_state.get("prob_healthy"),
        "prob_diseased": result_state.get("prob_diseased"),
        "severity": result_state.get("severity"),
        "recommendations": result_state.get("recommendations", []),
        "summary": result_state.get("summary"),
        "prompt": result_state.get("prompt"),
        "report_path": result_state.get("report_path"),
        "report": result_state.get("report"),
        "prediction_breakdown": result_state.get("prediction"),
        "shap_heatmap_path": shap_path,
        "shap_heatmap_base64": shap_base64,
        "shap_method": result_state.get("shap_method"),
        "shap_note": result_state.get("shap_note"),
    }

    return {"result": payload}

@app.post("/validate-image")
async def validate_image(file: UploadFile = File(...)):
    
    file_bytes = await file.read()
    val_result = check_image_corruption(file_bytes)
    return val_result
