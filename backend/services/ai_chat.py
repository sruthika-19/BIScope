import os
from typing import List, Dict
from services.terminology import analyze_query
from services.bis_data import search_standards

def get_groq_client():
    try:
        from groq import Groq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        return Groq(api_key=api_key)
    except ImportError:
        return None

def chat_with_ai(user_message: str, conversation_history: List[Dict[str, str]] = None) -> dict:
    history = conversation_history or []
    
    # 1. Build context for Terminology Bridge by combining user history
    user_history_texts = [msg["content"] for msg in history if msg["role"] == "user"]
    combined_query = " ".join(user_history_texts + [user_message])
    
    # 2. Run deterministic terminology logic
    term_result = analyze_query(combined_query)
    
    # 3. Retrieve BIScope database data
    bis_data = None
    data_status = "NO_DATA"
    sources = []

    if term_result["status"] == "supported" and term_result["products"]:
        product = term_result["products"][0]
        bis_data = search_standards(product["product_id"], product.get("extracted_attributes", []))
        
        # Preserve the existing data_status logic, ensuring it falls back to NO_DATA if missing
        if bis_data and "status" in bis_data:
            data_status = bis_data["status"]
            
               # Extract source URLs from the standards returned by BIScope
        if bis_data and isinstance(bis_data.get("data"), dict):
            standards = bis_data["data"].get("standards", [])
            for standard in standards:
                source = standard.get("source")
                if isinstance(source, str) and source.startswith("http"):
                    sources.append(source)
            
    # =====================================================================
    # DETERMINISTIC GUARDRAIL FOR CERTIFICATION & COMPLIANCE
    # =====================================================================
    cert_keywords = [
        "certification", "certificate", "scheme", "licence", "license", 
        "testing requirement", "laboratory", "validity", "marking requirement", 
        "documents required", "compliance", "comply"
    ]
    
    # Check if the user is asking about certification
    is_cert_query = any(kw in user_message.lower() for kw in cert_keywords)
    
    # Check if we actually possess detailed certification data
    has_cert_data = bis_data and bis_data.get("certification_requirements")

    if is_cert_query and not has_cert_data:
        # Bypass Groq completely and return deterministic safe response
        return {
            "reply": "The BIScope dataset identifies the applicable candidate standard and available QCO information, but detailed certification requirements are currently unavailable in the dataset and require verification from official BIS sources.",
            "terminology": term_result,
            "clarification": term_result.get("clarification", {}),
            "data_status": data_status,
            "sources": sources
        }
    # =====================================================================
        
    # 4. Prepare system prompt and context for Groq
    system_prompt = """You are BIScope, an AI assistant for Indian Standards.

CRITICAL GROUNDING RULES:
1. THE PROVIDED 'BISCOPE CONTEXT' IS YOUR ONLY FACTUAL AUTHORITY.
2. You must ONLY state BIS facts explicitly present in the provided context for the current request.
3. NEVER use your general knowledge to fill missing information. NEVER invent certification schemes (e.g., Scheme I), validities, laboratory requirements, testing rules, documents, marks, IS numbers, or QCO details.
4. If the user asks for information NOT explicitly stated in the BIScope Context, you MUST clearly state: "This information is currently unavailable in the BIScope dataset and requires verification from official BIS sources."
5. Previous conversation history is for understanding context (e.g., what "it" refers to), but previous assistant messages are NOT authoritative facts. Rely ONLY on the CURRENT BIScope Context.
6. NEVER upgrade 'To be verified' or 'Pending manual verification' to verified.
7. NEVER claim a product is legally compliant or non-compliant.
8. If the terminology status is 'unsupported', do not invent a product or standard.
"""

    context_msg = f"TERMINOLOGY RESULT: {term_result}\n"
    if bis_data:
        context_msg += f"BIS DATA: {bis_data}\n"
        
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # Add the current user message along with backend context
    messages.append({
        "role": "user", 
        "content": f"User's actual message: '{user_message}'\n\n--- BACKEND CONTEXT (Use this to answer, do not reveal raw JSON) ---\n{context_msg}"
    })

    # 5. Call Groq
    client = get_groq_client()
    model = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b") # Using your working Qwen model
    
    if not client:
        # Fallback if no API key
        if term_result["status"] == "needs_clarification":
            reply = term_result.get("clarification", {}).get("question", "Please clarify your request.")
        elif term_result["status"] == "supported":
            reply = "I identified your product. [DEVELOPMENT MOCK DATA: Groq API key missing, cannot generate natural response]"
        else:
            reply = "I couldn't identify the specific BIS product. [Groq API key missing]"
    else:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=500
            )
            # THIS IS THE FIX: This line is now strictly inside the try block
            reply = response.choices[0].message.content
            
            # Prevent blank responses
            if not reply or not reply.strip():
                reply = "I identified your product, but the AI model returned an empty response."
        except Exception as e:
            reply = f"I am experiencing network issues communicating with my AI model. Error: {str(e)}"
            
    return {
        "reply": reply,
        "terminology": term_result,
        "clarification": term_result.get("clarification", {}),
        "data_status": data_status,
        "sources": sources
    }