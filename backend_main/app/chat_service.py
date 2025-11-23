from typing import Dict, List, Optional
import os
from google import genai
from dotenv import load_dotenv
from ddgs import DDGS

# Load environment variables FIRST
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

print(f"[CHAT SERVICE INIT] GEMINI_API_KEY loaded: {'Yes' if api_key else 'No'}")
print(f"[CHAT SERVICE INIT] Using DuckDuckGo for web search (India-focused)")

client = genai.Client(api_key=api_key)

# In-memory chat storage
_chat_sessions: Dict[str, Dict] = {}

# ================================================================
#                    DUCKDUCKGO WEB SEARCH (INDIA-FOCUSED)
# ================================================================
def search_web(query: str, num_results: int = 5) -> List[Dict]:
    """
    Search the web using DuckDuckGo with India region focus
    
    Returns:
        List of search results with title, snippet, and link
    """
    print(f"\n[DUCKDUCKGO] 🦆 Starting web search (India region)...")
    print(f"[DUCKDUCKGO] Query: '{query}'")
    print(f"[DUCKDUCKGO] Requested results: {num_results}")
    
    try:
        results = []
        
        # Add "India" context to query for better regional results
        india_query = f"{query} India"
        print(f"[DUCKDUCKGO] India-focused query: '{india_query}'")
        
        # Create DDGS instance and search with India region
        ddgs = DDGS()
        print(f"[DUCKDUCKGO] Sending search request with region=in-en...")
        
        search_results = list(ddgs.text(
            india_query,
            region='in-en',  # India English
            safesearch='moderate',
            max_results=num_results
        ))
        
        print(f"[DUCKDUCKGO] Raw results count: {len(search_results)}")
        
        for idx, result in enumerate(search_results, 1):
            search_result = {
                "title": result.get("title", ""),
                "snippet": result.get("body", ""),
                "link": result.get("href", "")
            }
            results.append(search_result)
            
            print(f"[DUCKDUCKGO] Result {idx}:")
            print(f"  Title: {search_result['title'][:80]}...")
            print(f"  Link: {search_result['link']}")
            print(f"  Snippet: {search_result['snippet'][:100]}...")
        
        print(f"[DUCKDUCKGO] ✅ Successfully retrieved {len(results)} results\n")
        return results
        
    except Exception as e:
        print(f"[DUCKDUCKGO] ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def should_search_web(user_message: str) -> bool:
    """
    Determine if the user's message requires web search.
    Triggers for: treatments, prevention methods, specific disease info, etc.
    """
    search_keywords = [
        "treatment", "cure", "prevent", "prevention", "how to",
        "what is", "latest", "research", "organic", "pesticide",
        "fertilizer", "fungicide", "spray", "chemical", "natural remedy",
        "home remedy", "best practice", "when to", "symptoms of",
        "causes of", "identify", "difference between", "compare",
        "buy", "price", "cost", "where to get", "recommend",
        "available", "market", "local", "nearby", "dealer"
    ]
    
    message_lower = user_message.lower()
    matched_keywords = [kw for kw in search_keywords if kw in message_lower]
    
    should_search = len(matched_keywords) > 0
    
    print(f"\n[SEARCH DECISION] Message: '{user_message[:60]}...'")
    print(f"[SEARCH DECISION] Should search web: {should_search}")
    if matched_keywords:
        print(f"[SEARCH DECISION] Matched keywords: {matched_keywords}")
    
    return should_search

# ================================================================
#                    SESSION MANAGEMENT
# ================================================================
def initialize_session(session_id: str, analysis_context: dict) -> dict:
    """Initialize a new chat session"""
    print(f"\n[SESSION INIT] 🆕 Creating new session: {session_id}")
    print(f"[SESSION INIT] Analysis context keys: {list(analysis_context.keys())}")
    
    pred_class = analysis_context.get("pred_class", "Unknown")
    severity = analysis_context.get("severity", "Unknown")
    recommendations = analysis_context.get("recommendations", [])
    summary = analysis_context.get("summary", "")
    
    print(f"[SESSION INIT] Prediction: {pred_class}")
    print(f"[SESSION INIT] Severity: {severity}")
    print(f"[SESSION INIT] Recommendations count: {len(recommendations)}")
    
    if pred_class.lower() == "healthy":
        initial_message = f"🌱 Great news! Your plant appears to be healthy. {summary if summary else 'I can help answer any questions about plant care and prevention specific to Indian agriculture.'}"
    else:
        initial_message = f"🔍 I've analyzed your plant and detected **{pred_class}** with **{severity} severity**.\n\n{summary if summary else ''}\n\n**Recommendations for Indian Climate:**\n" + "\n".join(f"• {rec}" for rec in recommendations[:3])
        initial_message += "\n\n💡 **Ask me about:**\n• Treatments available in India\n• Local pesticides and fungicides\n• Organic solutions\n• Weather-specific advice\n• Where to buy supplies locally\n\nI can search Indian agricultural resources for the latest information! 🇮🇳"
    
    _chat_sessions[session_id] = {
        "analysis_context": analysis_context,
        "history": [
            {"role": "assistant", "content": initial_message, "timestamp": ""}
        ]
    }
    
    print(f"[SESSION INIT] ✅ Session created with {len(_chat_sessions[session_id]['history'])} messages")
    print(f"[SESSION INIT] Total active sessions: {len(_chat_sessions)}\n")
    
    return _chat_sessions[session_id]

def send_message(session_id: str, user_message: str) -> dict:
    """Send a message and get AI response with optional web search (India-focused)"""
    print(f"\n[SEND MESSAGE] 📨 Session: {session_id}")
    print(f"[SEND MESSAGE] User message: '{user_message[:100]}...'")
    
    if session_id not in _chat_sessions:
        print(f"[SEND MESSAGE] ❌ ERROR: Session not found")
        return {"error": "Session not found", "session_expired": True}
    
    session = _chat_sessions[session_id]
    print(f"[SEND MESSAGE] Current history length: {len(session['history'])}")
    
    session["history"].append({"role": "user", "content": user_message, "timestamp": ""})
    
    try:
        analysis_context = session["analysis_context"]
        
        # Check if we should perform web search
        web_results = []
        search_context = ""
        
        if should_search_web(user_message):
            # Build search query based on disease context
            disease_name = analysis_context.get("pred_class", "")
            
            # Clean up disease name for better search results
            clean_disease = disease_name.replace("___", " ").replace("_", " ")
            
            # Only use disease context if it's specific (not "DISEASED" or "HEALTHY")
            if disease_name.upper() in ["DISEASED", "HEALTHY", "UNKNOWN"]:
                # Use generic plant disease query
                search_query = f"plant disease {user_message}"
                print(f"[SEND MESSAGE] Using generic plant disease query (disease type: {disease_name})")
            else:
                # Use specific disease name
                search_query = f"{clean_disease} {user_message}"
            
            print(f"[SEND MESSAGE] 🌐 Triggering web search (India-focused)...")
            print(f"[SEND MESSAGE] Disease context: {disease_name}")
            print(f"[SEND MESSAGE] Clean disease name: {clean_disease}")
            print(f"[SEND MESSAGE] Final search query: '{search_query}'")
            
            web_results = search_web(search_query, num_results=5)
            
            if web_results:
                print(f"[SEND MESSAGE] ✅ Web search returned {len(web_results)} results")
                search_context = "\n\n🌐 **Web Search Results from Indian Sources:**\n"
                for i, result in enumerate(web_results, 1):
                    search_context += f"\n**Result {i}:** {result['title']}\n"
                    search_context += f"   📝 {result['snippet'][:250]}...\n"
                    search_context += f"   🔗 Source: {result['link']}\n"
                print(f"[SEND MESSAGE] Search context length: {len(search_context)} chars")
            else:
                print(f"[SEND MESSAGE] ⚠️ Web search returned no results, will use AI knowledge only")
        else:
            print(f"[SEND MESSAGE] ℹ️ No web search needed for this query")
        
        # Build prompt with search results (INDIA-SPECIFIC)
        print(f"[SEND MESSAGE] 🤖 Building Gemini prompt (India-focused)...")
        
        context_prompt = f"""You are AgriGuard Assistant, an expert agricultural AI specifically helping Indian farmers with plant health issues in the Indian climate and agricultural context.

        **IMPORTANT CONTEXT - INDIA-SPECIFIC:**
        - Focus on solutions, products, and practices available in India
        - Consider Indian climate zones (tropical, subtropical, temperate)
        - Reference Indian agricultural institutions (ICAR, state agricultural universities)
        - Mention locally available pesticides, fungicides, and organic solutions
        - Consider Indian cropping seasons (Kharif, Rabi, Zaid)
        - Price recommendations in Indian Rupees (₹)
        - Reference Indian agricultural markets and dealers

        Analysis Context:
        - Prediction: {analysis_context.get('pred_class', 'Unknown')}
        - Severity: {analysis_context.get('severity', 'Unknown')}
        - Recommendations: {', '.join(analysis_context.get('recommendations', []))}
        - Summary: {analysis_context.get('summary', '')}

        Conversation History:
        """
        for msg in session["history"][:-1]:
            context_prompt += f"{msg['role'].title()}: {msg['content']}\n"
        
        context_prompt += f"\nUser (Indian Farmer): {user_message}\n"
        
        # Add web search results if available
        if search_context:
            print(f"[SEND MESSAGE] Adding web search context to prompt")
            context_prompt += f"\n{search_context}\n"
            context_prompt += "\n**Instructions:** Using the web search results above (focused on Indian sources), provide a comprehensive answer that:\n"
            context_prompt += "1. **Prioritizes Indian context** - products available in India, Indian brands, local dealers\n"
            context_prompt += "2. **Cites specific sources** from the search results (e.g., 'According to [Source Title]...')\n"
            context_prompt += "3. **Provides actionable advice** with specific steps suitable for Indian farmers\n"
            context_prompt += "4. **Mentions prices in ₹ (Indian Rupees)** if discussing products\n"
            context_prompt += "5. **Considers Indian climate** and seasonal variations (monsoon, summer, winter)\n"
            context_prompt += "6. **References Indian institutions** like ICAR, KVK (Krishi Vigyan Kendra), state agriculture departments\n"
            context_prompt += "7. **Keeps the response conversational** but informative (4-6 sentences)\n"
            context_prompt += "8. **Mentions which result number** you're referencing (e.g., 'Based on Result 1...')\n"
        else:
            context_prompt += "\n**Instructions:** Provide a helpful, India-specific response (3-4 sentences) that:\n"
            context_prompt += "1. Focuses on solutions available in India\n"
            context_prompt += "2. Considers Indian climate and agricultural practices\n"
            context_prompt += "3. Mentions Indian brands/products when relevant\n"
            context_prompt += "4. Uses Indian Rupees (₹) for pricing\n"
            context_prompt += "5. References Indian agricultural resources (ICAR, KVK, etc.)\n"
        
        print(f"[SEND MESSAGE] Final prompt length: {len(context_prompt)} chars")
        print(f"[SEND MESSAGE] Calling Gemini API...")
        
        # Call Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context_prompt
        )
        
        assistant_message = response.text
        print(f"[SEND MESSAGE] ✅ Gemini response received: {len(assistant_message)} chars")
        
        # Add web results indicator if search was performed
        if web_results:
            assistant_message += "\n\n---\n🇮🇳 **Indian Sources Referenced:**"
            print(f"[SEND MESSAGE] Added sources indicator to response")
        
        session["history"].append({"role": "assistant", "content": assistant_message, "timestamp": ""})
        
        result = {
            "response": assistant_message,
            "session_id": session_id,
            "message_count": len(session["history"]),
            "web_search_performed": len(web_results) > 0,
            "sources": [{"title": r["title"], "link": r["link"]} for r in web_results] if web_results else []
        }
        
        print(f"[SEND MESSAGE] ✅ Success! Returning India-focused response with {len(result.get('sources', []))} sources")
        print(f"[SEND MESSAGE] Total messages in session: {result['message_count']}\n")
        
        return result
        
    except Exception as e:
        print(f"[SEND MESSAGE] ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        fallback = "मुझे खेद है (I apologize), but I'm having trouble generating a response right now. Please try rephrasing your question or ask about specific Indian agricultural products/practices."
        session["history"].append({"role": "assistant", "content": fallback, "timestamp": ""})
        
        return {
            "response": fallback, 
            "session_id": session_id, 
            "error": str(e),
            "web_search_performed": False,
            "sources": []
        }

def get_chat_history(session_id: str) -> Optional[List[dict]]:
    """Get chat history for a session"""
    print(f"\n[GET HISTORY] 📜 Session: {session_id}")
    
    if session_id not in _chat_sessions:
        print(f"[GET HISTORY] ❌ Session not found")
        return None
    
    history = _chat_sessions[session_id]["history"]
    print(f"[GET HISTORY] ✅ Returning {len(history)} messages\n")
    
    return history

def clear_session(session_id: str) -> bool:
    """Clear a chat session"""
    print(f"\n[CLEAR SESSION] 🗑️ Session: {session_id}")
    
    if session_id in _chat_sessions:
        del _chat_sessions[session_id]
        print(f"[CLEAR SESSION] ✅ Session cleared")
        print(f"[CLEAR SESSION] Remaining active sessions: {len(_chat_sessions)}\n")
        return True
    
    print(f"[CLEAR SESSION] ❌ Session not found\n")
    return False