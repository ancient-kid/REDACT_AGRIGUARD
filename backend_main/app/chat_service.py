from typing import Dict, List, Optional
import os
from google import genai
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


# In-memory chat storage
_chat_sessions: Dict[str, Dict] = {}

def initialize_session(session_id: str, analysis_context: dict) -> dict:
    """Initialize a new chat session"""
    pred_class = analysis_context.get("pred_class", "Unknown")
    severity = analysis_context.get("severity", "Unknown")
    recommendations = analysis_context.get("recommendations", [])
    summary = analysis_context.get("summary", "")
    
    if pred_class.lower() == "healthy":
        initial_message = f"Great news! Your plant appears to be healthy. {summary if summary else 'I can help answer any questions about plant care and prevention.'}"
    else:
        initial_message = f"I've analyzed your plant and detected {pred_class} with {severity} severity. {summary if summary else ''}\n\nRecommendations:\n" + "\n".join(f"• {rec}" for rec in recommendations[:3])
        initial_message += "\n\nFeel free to ask me about treatments, prevention, or any specific concerns!"
    
    _chat_sessions[session_id] = {
        "analysis_context": analysis_context,
        "history": [
            {"role": "assistant", "content": initial_message, "timestamp": ""}
        ]
    }
    
    return _chat_sessions[session_id]

def send_message(session_id: str, user_message: str) -> dict:
    """Send a message and get AI response"""
    if session_id not in _chat_sessions:
        return {"error": "Session not found", "session_expired": True}
    
    session = _chat_sessions[session_id]
    session["history"].append({"role": "user", "content": user_message, "timestamp": ""})
    
    try:
        analysis_context = session["analysis_context"]
        context_prompt = f"""You are AgriGuard Assistant, an expert agricultural AI helping farmers with plant health.

Analysis Context:
- Prediction: {analysis_context.get('pred_class', 'Unknown')}
- Severity: {analysis_context.get('severity', 'Unknown')}
- Recommendations: {', '.join(analysis_context.get('recommendations', []))}
- Summary: {analysis_context.get('summary', '')}

Conversation History:
"""
        for msg in session["history"][:-1]:
            context_prompt += f"{msg['role'].title()}: {msg['content']}\n"
        
        context_prompt += f"\nUser: {user_message}\n\nProvide a helpful, concise response (2-3 sentences) about plant care, treatments, or the analysis."
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context_prompt
        )
        
        assistant_message = response.text
        session["history"].append({"role": "assistant", "content": assistant_message, "timestamp": ""})
        
        return {
            "response": assistant_message,
            "session_id": session_id,
            "message_count": len(session["history"])
        }
        
    except Exception as e:
        fallback = "I apologize, but I'm having trouble generating a response right now."
        session["history"].append({"role": "assistant", "content": fallback, "timestamp": ""})
        return {"response": fallback, "session_id": session_id, "error": str(e)}

def get_chat_history(session_id: str) -> Optional[List[dict]]:
    """Get chat history for a session"""
    if session_id not in _chat_sessions:
        return None
    return _chat_sessions[session_id]["history"]

def clear_session(session_id: str) -> bool:
    """Clear a chat session"""
    if session_id in _chat_sessions:
        del _chat_sessions[session_id]
        return True
    return False