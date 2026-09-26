import os
import logging
import re
from typing import List, Dict
from services.terminology import analyze_query
from services.bis_data import search_standards
from services.detailed_requirements import get_detailed_requirements

logger = logging.getLogger(__name__)
GROQ_TIMEOUT_SECONDS = 8.0
BISCOPE_APPLICATION_FACTS = {
    "description": "an AI-powered assistant for Indian Standards and BIS services",
    "capabilities": (
        "find relevant candidate standards",
        "review available requirements",
        "compare supporting evidence",
        "identify next steps",
    ),
    "verification_note": "Details marked for verification should be confirmed with official BIS sources.",
}


def _question_for_intent(user_message: str) -> str:
    question_marker = "User question:"
    if question_marker not in user_message:
        return user_message

    question = user_message.split(question_marker, 1)[1]
    context_marker = "BIScope context:"
    if context_marker in question:
        question = question.split(context_marker, 1)[0]
    return question.strip()


def _is_biscope_general_question(question: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()
    patterns = (
        r"\btell me about biscope\b",
        r"\bdescribe biscope\b",
        r"\bwhat is biscope\b",
        r"\bwhat can (?:biscope|you) do\b",
        r"\bwhat does biscope do\b",
        r"\bhow does biscope work\b",
        r"\bhow does biscope help\b",
        r"\bwhat are the features of biscope\b",
        r"\bwhat features does biscope have\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _is_general_bis_question(question: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()
    return bool(re.fullmatch(r"what is bis", normalized))


def _biscope_application_reply() -> str:
    capabilities = BISCOPE_APPLICATION_FACTS["capabilities"]
    capability_list = ", ".join(capabilities[:-1]) + f", and {capabilities[-1]}"
    return (
        f"BIScope is {BISCOPE_APPLICATION_FACTS['description']}. "
        f"It helps users {capability_list} using BIS-backed data. "
        f"{BISCOPE_APPLICATION_FACTS['verification_note']}"
    )


def _frontend_context(user_message: str) -> str:
    context_marker = "BIScope context:"
    if context_marker not in user_message:
        return ""
    return user_message.split(context_marker, 1)[1].strip()

def _context_summary(user_message: str) -> str:
    context = _frontend_context(user_message)
    prefixes = (
        "Product:",
        "Currently selected candidate standard:",
        "Standard record lifecycle:",
        "Scope:",
        "Standard source:",
        "Why this standard:",
        "Alternatives:",
        "Detailed requirements:",
        "Evidence mapping:",
    )
    facts = [
        line.strip()
        for line in context.splitlines()
        if line.strip().startswith(prefixes)
    ]
    facts = [
        line.split(" Do not describe", 1)[0].rstrip()
        if line.startswith("Standard record lifecycle:")
        else line
        for line in facts
    ]
    if facts:
        return "\n".join(f"- {fact}" for fact in facts)
    return ""

def _deterministic_data_reply(
    user_message: str,
    term_result: dict,
    bis_data: dict | None,
) -> str:
    if term_result.get("status") == "needs_clarification":
        return term_result.get("clarification", {}).get(
            "question", "Please clarify your product description."
        )

    context_summary = _context_summary(user_message)
    if context_summary:
        return (
            "Based on the available BIScope data:\n\n"
            f"{context_summary}\n\n"
            "The listed status and applicability still require verification where indicated; "
            "this is not a compliance or certification determination."
        )

    products = term_result.get("products") or []
    if term_result.get("status") == "supported" and products:
        product = products[0]
        product_name = product.get("normalized_term", "Supported product")
        product_id = product.get("product_id", "")
        lines = [f"- Product: {product_name} ({product_id})"]
        standards = ((bis_data or {}).get("data") or {}).get("standards") or []
        if standards:
            standard = standards[0]
            standard_number = standard.get("standard_number", "not available")
            lines.append(
                f"- Candidate standard: {standard_number}; "
                f"status: {standard.get('status') or 'To be verified'}"
            )
        detailed = get_detailed_requirements(product_id)
        requirements = (detailed or {}).get("requirements", [])
        if requirements:
            lines.append(
                f"- Detailed requirements: {len(requirements)} records for "
                f"{detailed.get('standard_number', 'the selected standard')}"
            )
            lines.extend(
                f"  - {item['requirement_id']}: {item['requirement_description']}"
                for item in requirements
            )
        lines.append(
            "- Verify technical applicability and certification information against official BIS sources."
        )
        return (
            "Based on the available BIScope data:\n\n"
            + "\n".join(lines)
            + "\n\nThis is not a compliance or certification determination."
        )

    return (
        "This information is not available in the current BIScope context. "
        "Describe a supported product or provide more detail to continue."
    )

def get_groq_client():
    try:
        from groq import Groq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        return Groq(
            api_key=api_key,
            timeout=GROQ_TIMEOUT_SECONDS,
            max_retries=0,
        )
    except ImportError:
        return None

def chat_with_ai(user_message: str, conversation_history: List[Dict[str, str]] = None) -> dict:
    question_for_intent = _question_for_intent(user_message)
    if _is_biscope_general_question(question_for_intent) or _is_general_bis_question(question_for_intent):
        is_bis_definition = _is_general_bis_question(question_for_intent)
        return {
            "reply": (
                "BIS is the Bureau of Indian Standards, India's national standards body. "
                "BIScope helps users explore Indian Standards and related BIS services."
                if is_bis_definition
                else _biscope_application_reply()
            ),
            "terminology": {
                "status": "not_applicable",
                "products": [],
                "normalized_query": question_for_intent,
                "clarification": {"needed": False, "question": None, "reason": None},
            },
            "clarification": {"needed": False, "question": None, "reason": None},
            "data_status": "APPLICATION_INFO",
            "sources": [],
        }

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
    
    # Only classify the user's question, not frontend-provided safety/context text.
    is_cert_query = any(kw in question_for_intent.lower() for kw in cert_keywords)
    
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
        reply = _deterministic_data_reply(user_message, term_result, bis_data)
    else:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=500
            )
            reply = response.choices[0].message.content
            
            if not reply or not reply.strip():
                reply = _deterministic_data_reply(user_message, term_result, bis_data)
        except Exception as error:
            logger.warning(
                "Groq chat request failed (%s); returning a BIScope data-grounded response",
                type(error).__name__,
            )
            reply = _deterministic_data_reply(user_message, term_result, bis_data)
            
    return {
        "reply": reply,
        "terminology": term_result,
        "clarification": term_result.get("clarification", {}),
        "data_status": data_status,
        "sources": sources
    }