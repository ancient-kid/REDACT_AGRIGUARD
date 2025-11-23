# backend_main/app/main.py

import sys
import os
import base64
from pathlib import Path
import shutil
import uuid
from typing import Any, Dict
from . import chat_service
import cv2
import io

# Add missing imports for Grad-CAM
import torch
import numpy as np
from PIL import Image, ImageDraw
import torchvision.transforms as T

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from .validators import check_image_corruption
from .database import init_db, get_db, User, Upload, Chat, ChatMessage
from datetime import datetime
from shap_storage import store_shap_gradient


# Add project root and nodes folder to path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = PROJECT_ROOT / "agri_graph" / "nodes"
sys.path.append(str(NODES_PATH))

# Create uploads directory for storing images
UPLOADS_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

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


# Import Grad-CAM components - THIS MUST BE BEFORE gradcam_transform
from .agri_graph.nodes.multi_class_cnn import SimpleCNNMulti, DEVICE, IMG_SIZE

# Pydantic models for chat requests
class ChatInitRequest(BaseModel):
    analysis_context: dict

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class ChatHistoryRequest(BaseModel):
    session_id: str


# NOW IMG_SIZE is defined, so we can use it
gradcam_transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# ================================================================
#                       GRAD-CAM CLASS
# ================================================================
class GradCAM:
    """Grad-CAM for visualization"""
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
#          HELPER: LOAD DISEASE MODEL
# ================================================================
_disease_model_cache = None
_disease_class_names_cache = None

def load_disease_model_for_gradcam():
    """Load disease model once and cache it"""
    global _disease_model_cache, _disease_class_names_cache
    
    if _disease_model_cache is None:
        disease_model_path = PROJECT_ROOT / "best_disease_model.pth"
        ckpt = torch.load(disease_model_path, map_location=DEVICE)
        _disease_class_names_cache = ckpt["class_names"]
        _disease_model_cache = SimpleCNNMulti(num_classes=len(_disease_class_names_cache)).to(DEVICE)
        _disease_model_cache.load_state_dict(ckpt["model_state"])
        _disease_model_cache.eval()
        print(f"[GRADCAM] Loaded disease model from {disease_model_path}")
    
    return _disease_model_cache, _disease_class_names_cache

# ================================================================
#          HELPER: GET BBOX FROM CAM
# ================================================================
def get_bbox_from_cam(cam):
    """Extract bounding box from top-5% hottest CAM regions"""
    H, W = cam.shape
    cam_norm = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

    # Top 5% threshold
    thr = np.quantile(cam_norm, 0.95)
    binary = (cam_norm >= thr).astype(np.uint8)

    # Dilation to connect regions
    kernel = np.ones((15, 15), np.uint8)
    binary = cv2.dilate(binary, kernel, iterations=2)

    cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    c = max(cnts, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)

    # Add padding
    pad = 0.2
    pw, ph = int(w * pad), int(h * pad)
    x1 = max(0, x - pw)
    y1 = max(0, y - ph)
    x2 = min(W, x + w + pw)
    y2 = min(H, y + h + ph)

    return x1, y1, x2, y2

# ================================================================
#          HELPER: DRAW BBOX
# ================================================================
def draw_bbox_on_image(orig_img, cam):
    """Draw red bounding box on image based on CAM"""
    cam_up = cv2.resize(cam, (orig_img.width, orig_img.height))
    bbox = get_bbox_from_cam(cam_up)

    img = orig_img.copy()
    draw = ImageDraw.Draw(img)

    if bbox is None:
        print("[GRADCAM] No bbox found, returning image without box")
        return img

    x1, y1, x2, y2 = bbox
    draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0), width=10)
    return img

# Build the Graph
state_schema = dict
builder = StateGraph(state_schema)

builder.add_node("ImageInput", image_input)
builder.add_node("Preprocess", preprocess)
builder.add_node("ModelPredict", model_predict)
builder.add_node("DiseaseClassifier", disease_classification)
builder.add_node("SHAPExplain", shap_explain)
builder.add_node("RuleRecommender", recommender)
builder.add_node("LLMSummarize", llm_summarize)
builder.add_node("ReportOutput", report_output)

builder.add_edge(START, "ImageInput")
builder.add_edge("ImageInput", "Preprocess")
builder.add_edge("Preprocess", "ModelPredict")
builder.add_edge("ModelPredict", "DiseaseClassifier")
builder.add_edge("DiseaseClassifier", "SHAPExplain")
builder.add_edge("SHAPExplain", "RuleRecommender")
builder.add_edge("RuleRecommender", "LLMSummarize")
builder.add_edge("LLMSummarize", "ReportOutput")
builder.add_edge("ReportOutput", END)

compiled_graph = builder.compile()

app = FastAPI(title="AgriGuard Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

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

@app.post("/analyze/gradcam")
async def analyze_image_gradcam(file: UploadFile = File(...)):
    """
    Analyze uploaded image with Grad-CAM and return annotated image with bounding box.
    """
    try:
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG files are supported")
        
        contents = await file.read()
        orig_img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        model, class_names = load_disease_model_for_gradcam()
        
        img_tensor = gradcam_transform(orig_img).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            out = model(img_tensor)
            probs = torch.softmax(out, dim=1)
            cls_idx = torch.argmax(probs).item()
            cls_name = class_names[cls_idx]
            conf = probs[0][cls_idx].item()
        
        print(f"[GRADCAM] Predicted: {cls_name} (confidence: {conf:.3f})")
        
        target_layer = model.features[-2]
        grad_cam = GradCAM(model, target_layer)
        cam = grad_cam(img_tensor, cls_idx)
        
        annotated_img = draw_bbox_on_image(orig_img, cam)
        
        buffer = io.BytesIO()
        annotated_img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            "prediction": cls_name,
            "confidence": round(conf, 4),
            "annotated_image_base64": img_base64,
            "image_format": "png"
        }
        
    except Exception as e:
        import traceback
        print(f"[GRADCAM ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Grad-CAM analysis failed: {str(e)}")

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # Generate unique filename
    upload_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix if file.filename else '.jpg'
    stored_filename = f"{upload_id}{file_extension}"
    stored_path = UPLOADS_DIR / stored_filename
    
    # Save uploaded image temporarily for processing

    tmp_path = PROJECT_ROOT / "temp_upload.jpg"
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Also save a permanent copy
    shutil.copy(tmp_path, stored_path)

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


    try:
        os.remove(tmp_path)
    except Exception:
        pass

    payload = {
        "upload_id": upload_id,
        "stored_image_path": str(stored_path),
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

    archive_context = {
        "pred_class": result_state.get("pred_class"),
        "shap_method": result_state.get("shap_method"),
    }
    archive_path = store_shap_gradient(upload_id, shap_path, context=archive_context)
    if archive_path:
        print(f"[SHAP STORAGE] Archived gradient for {upload_id} -> {archive_path}")

    payload.update(initialize_chat_session_for_analysis(result_state))

    return {"result": payload}


def _build_chat_context_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "pred_class": state.get("pred_class", "Unknown"),
        "severity": state.get("severity", "Unknown"),
        "recommendations": state.get("recommendations", []),
        "summary": state.get("summary", ""),
    }


def initialize_chat_session_for_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    context = _build_chat_context_from_state(state)
    session_id = str(uuid.uuid4())
    session = chat_service.initialize_session(session_id, context)
    history = session.get("history", [])
    initial_message = history[0]["content"] if history else ""
    return {
        "chat_session_id": session_id,
        "chat_initial_message": initial_message
    }


@app.get("/dashboard/stats")
async def get_dashboard_statistics():
    from .dashboard_service import get_dashboard_stats
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard stats: {str(e)}")

@app.post("/chat/init")
async def initialize_chat(request: ChatInitRequest, db: Session = Depends(get_db)):
    """Initialize a new chat session"""
    try:
        # Use chat_service to initialize
        session_id = str(uuid.uuid4())
        session_data = chat_service.initialize_session(session_id, request.analysis_context)
        
        # Optionally: Store in database if user is authenticated
        # For now, just return the session
        
        return {
            "session_id": session_id,
            "initial_message": session_data["history"][0]["content"],
            "status": "initialized"
        }
    except Exception as e:
        print(f"[CHAT INIT ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize chat: {str(e)}")


@app.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a session"""
    history = chat_service.get_chat_history(session_id)
    
    if history is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return {
        "session_id": session_id,
        "history": history
    }


@app.post("/chat/history")
async def get_chat_history(request: ChatHistoryRequest):
    history = chat_service.get_chat_history(request.session_id)  # ❌ chat_service doesn't exist
    
    if history is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return {
        "session_id": request.session_id,
        "history": history
    }

@app.delete("/chat/{session_id}")
async def clear_chat_session(session_id: str, db: Session = Depends(get_db)):
    """Clear a chat session"""
    success = chat_service.clear_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": "cleared"
    }

@app.post("/validate-image")
async def validate_image(file: UploadFile = File(...)):
    file_bytes = await file.read()
    val_result = check_image_corruption(file_bytes)
    return val_result

@app.post("/chat/{session_id}/message")
async def send_chat_message(session_id: str, request: ChatMessageRequest, db: Session = Depends(get_db)):
    """Send a message in existing chat session"""
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Use chat_service to handle the message
        result = chat_service.send_message(session_id, request.message)
        
        if "error" in result:
            if result.get("session_expired"):
                raise HTTPException(status_code=404, detail=result["error"])
            
            print(result)
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Optionally: Store messages in database here if needed
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT MESSAGE ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


# ========== Dashboard API Endpoints ==========

class UserCreateRequest(BaseModel):
    user_id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None

class UploadCreateRequest(BaseModel):
    user_id: str
    file_name: str
    image_path: str | None = None
    prediction_class: str
    severity: str
    confidence_healthy: float
    confidence_diseased: float
    summary: str | None = None

class ChatCreateRequest(BaseModel):
    user_id: str
    session_id: str

class ChatMessageCreateRequest(BaseModel):
    chat_id: str
    role: str
    content: str


@app.post("/api/users")
async def create_or_get_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    """Create user if not exists, or return existing user"""
    user = db.query(User).filter(User.user_id == request.user_id).first()
    if not user:
        user = User(
            user_id=request.user_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"user_id": user.user_id, "email": user.email}


@app.post("/api/uploads")
async def create_upload(request: UploadCreateRequest, db: Session = Depends(get_db)):
    """Save upload history"""
    upload = Upload(
        id=str(uuid.uuid4()),
        user_id=request.user_id,
        file_name=request.file_name,
        image_path=request.image_path,
        prediction_class=request.prediction_class,
        severity=request.severity,
        confidence_healthy=request.confidence_healthy,
        confidence_diseased=request.confidence_diseased,
        summary=request.summary
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    
    return {
        "id": upload.id,
        "timestamp": upload.timestamp.isoformat()
    }


@app.get("/api/uploads/{user_id}")
async def get_uploads(user_id: str, db: Session = Depends(get_db)):
    """Get all uploads for a user"""
    uploads = db.query(Upload).filter(Upload.user_id == user_id).order_by(Upload.timestamp.desc()).all()
    
    return {
        "uploads": [
            {
                "id": u.id,
                "fileName": u.file_name,
                "imageUrl": f"/api/images/{u.id}" if u.image_path else None,
                "predictionClass": u.prediction_class,
                "severity": u.severity,
                "confidence": {
                    "healthy": u.confidence_healthy,
                    "diseased": u.confidence_diseased
                },
                "summary": u.summary,
                "timestamp": u.timestamp.isoformat()
            }
            for u in uploads
        ]
    }


@app.post("/api/chats")
async def create_chat(request: ChatCreateRequest, db: Session = Depends(get_db)):
    """Create a new chat session"""
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=request.user_id,
        session_id=request.session_id
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    
    return {
        "id": chat.id,
        "session_id": chat.session_id,
        "created_at": chat.created_at.isoformat()
    }


@app.get("/api/chats/{user_id}")
async def get_chats(user_id: str, db: Session = Depends(get_db)):
    """Get all chats for a user with their messages"""
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).all()
    
    result = []
    for chat in chats:
        messages = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).order_by(ChatMessage.timestamp).all()
        
        result.append({
            "id": chat.id,
            "sessionId": chat.session_id,
            "createdAt": chat.created_at.isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in messages
            ]
        })
    
    return {"chats": result}


@app.post("/api/chat-messages")
async def add_chat_message(request: ChatMessageCreateRequest, db: Session = Depends(get_db)):
    """Add a message to a chat"""
    message = ChatMessage(
        chat_id=request.chat_id,
        role=request.role,
        content=request.content
    )
    db.add(message)
    
    # Update chat's updated_at
    chat = db.query(Chat).filter(Chat.id == request.chat_id).first()
    if chat:
        chat.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    
    return {
        "id": message.id,
        "timestamp": message.timestamp.isoformat()
    }


@app.get("/api/dashboard-stats/{user_id}")
async def get_dashboard_stats(user_id: str, db: Session = Depends(get_db)):
    """Get dashboard statistics for a user"""
    uploads = db.query(Upload).filter(Upload.user_id == user_id).all()
    chats = db.query(Chat).filter(Chat.user_id == user_id).all()
    
    healthy_count = sum(1 for u in uploads if u.prediction_class.lower() == "healthy")
    diseased_count = sum(1 for u in uploads if u.prediction_class.lower() != "healthy")
    
    return {
        "totalUploads": len(uploads),
        "healthyPlants": healthy_count,
        "diseasedPlants": diseased_count,
        "totalChats": len(chats)
    }


@app.get("/api/images/{upload_id}")
async def get_upload_image(upload_id: str, db: Session = Depends(get_db)):
    """Serve stored upload image"""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if not upload or not upload.image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_path = Path(upload.image_path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    
    return FileResponse(image_path)

