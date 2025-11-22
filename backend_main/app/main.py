# backend_main/app/main.py

import sys
import os
import base64
from pathlib import Path
import shutil
import uuid
from typing import Dict

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# In-memory storage for chat sessions
chat_sessions: Dict[str, Dict] = {}

# Pydantic models for chat
class ChatInitRequest(BaseModel):
    analysis_context: dict

class ChatMessageRequest(BaseModel):
    message: str


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

@app.post("/chat/init")
async def initialize_chat(request: ChatInitRequest):
    """Initialize a new chat session with analysis context"""
    session_id = str(uuid.uuid4())
    
    # Extract relevant information from analysis context
    analysis = request.analysis_context
    pred_class = analysis.get("pred_class", "Unknown")
    severity = analysis.get("severity", "Unknown")
    recommendations = analysis.get("recommendations", [])
    summary = analysis.get("summary", "")
    
    # Create initial message based on analysis
    if pred_class.lower() == "healthy":
        initial_message = f"Great news! Your plant appears to be healthy. {summary if summary else 'I can help answer any questions about plant care and prevention.'}"
    else:
        initial_message = f"I've analyzed your plant and detected {pred_class} with {severity} severity. {summary if summary else ''}\n\nRecommendations:\n" + "\n".join(f"• {rec}" for rec in recommendations[:3])
        initial_message += "\n\nFeel free to ask me about treatments, prevention, or any specific concerns!"
    
    # Store session
    chat_sessions[session_id] = {
        "analysis_context": analysis,
        "messages": [
            {"role": "assistant", "content": initial_message}
        ]
    }
    
    return {
        "session_id": session_id,
        "initial_message": initial_message
    }

@app.post("/chat/{session_id}/message")
async def send_chat_message(session_id: str, request: ChatMessageRequest):
    """Send a message in an existing chat session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[session_id]
    user_message = request.message
    
    # Add user message to history
    session["messages"].append({"role": "user", "content": user_message})
    
    # Generate response using Gemini
    try:
        from google import genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        client = genai.Client(api_key=api_key)
        
        # Build conversation context
        analysis_context = session["analysis_context"]
        context_prompt = f"""You are AgriGuard Assistant, an expert agricultural AI helping farmers with plant health.

Analysis Context:
- Prediction: {analysis_context.get('pred_class', 'Unknown')}
- Severity: {analysis_context.get('severity', 'Unknown')}
- Recommendations: {', '.join(analysis_context.get('recommendations', []))}
- Summary: {analysis_context.get('summary', '')}

Conversation History:
"""
        for msg in session["messages"][:-1]:  # Exclude the last user message we just added
            context_prompt += f"{msg['role'].title()}: {msg['content']}\n"
        
        context_prompt += f"\nUser: {user_message}\n\nProvide a helpful, concise response (2-3 sentences) about plant care, treatments, or the analysis."
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=context_prompt
        )
        
        assistant_message = response.text
        
        # Add assistant response to history
        session["messages"].append({"role": "assistant", "content": assistant_message})
        
        return {
            "response": assistant_message,
            "session_id": session_id
        }
        
    except Exception as e:
        # Fallback response if Gemini fails
        fallback_response = "I apologize, but I'm having trouble generating a response right now. Please try rephrasing your question or contact support if the issue persists."
        session["messages"].append({"role": "assistant", "content": fallback_response})
        
        return {
            "response": fallback_response,
            "session_id": session_id,
            "error": str(e)
        }
