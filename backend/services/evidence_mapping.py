import re
from typing import Dict, List, Any, Optional

def normalize_text(text: Optional[str]) -> str:
    """Lowercases, strips, and removes unnecessary whitespace."""
    if not text:
        return ""
    text = str(text).lower()
    return re.sub(r'\s+', ' ', text).strip()

def extract_evidence_keywords(required_evidence: str) -> List[str]:
    """
    Derives meaningful keywords from the required evidence description deterministically.
    Ignores common stop words and short generic terms.
    """
    if not required_evidence:
        return []
    
    text = normalize_text(required_evidence)
    # Ignore generic terms to focus on the specific type of evidence required
    stop_words = {"test", "report", "the", "and", "for", "with", "from", "analysis"}
    words = text.split()
    
    # Keep words longer than 2 characters that are not in the stop_words set
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    return keywords

def compare_evidence(required_evidence: str, submitted_evidence: Optional[str]) -> Dict[str, Any]:
    """
    Compares the required evidence against submitted document text.
    Strictly identifies presence of keywords; does NOT verify authenticity or compliance.
    """
    req_keywords = extract_evidence_keywords(required_evidence)
    
    if not submitted_evidence or not submitted_evidence.strip():
        return {
            "status": "Missing",
            "evidence_status": "Not found",
            "message": "No evidence submitted. Upload required.",
            "matched_terms": [],
            "missing_terms": req_keywords
        }
    
    norm_submitted = normalize_text(submitted_evidence)
    matched = []
    missing = []
    
    for kw in req_keywords:
        if kw in norm_submitted:
            matched.append(kw)
        else:
            missing.append(kw)
            
    if not req_keywords:
        return {
            "status": "Needs review",
            "evidence_status": "Needs review",
            "message": "No specific evidence keywords to map. Manual review required.",
            "matched_terms": [],
            "missing_terms": []
        }

    ratio = len(matched) / len(req_keywords)
    
    # Exact phrase match or all keywords found
    if ratio == 1.0 or normalize_text(required_evidence) in norm_submitted:
        return {
            "status": "Matched",
            "evidence_status": "Evidence found",
            "message": "Relevant evidence terms detected. Manual verification of authenticity and technical limits is required.",
            "matched_terms": matched,
            "missing_terms": missing
        }
    elif ratio > 0:
        return {
            "status": "Partially matched",
            "evidence_status": "Needs review",
            "message": "Partial text overlap detected. Some required concepts are missing.",
            "matched_terms": matched,
            "missing_terms": missing
        }
    else:
        return {
            "status": "Needs review",
            "evidence_status": "Needs review",
            "message": "No confident textual match found. Manual review required.",
            "matched_terms": [],
            "missing_terms": missing
        }

def map_document_to_requirements(requirements: List[Dict[str, Any]], submitted_document_text: str) -> List[Dict[str, Any]]:
    """
    Maps a submitted document's text against a complete list of product requirements.
    """
    results = []
    for req in requirements:
        req_id = req.get("requirement_id", "UNKNOWN")
        req_desc = req.get("requirement_description", "")
        req_evid = req.get("required_evidence", "")
        evid_type = req.get("evidence_type", "")
        
        comp = compare_evidence(req_evid, submitted_document_text)
        
        results.append({
            "requirement_id": req_id,
            "requirement_description": req_desc,
            "required_evidence": req_evid,
            "evidence_type": evid_type,
            "status": comp["status"],
            "evidence_status": comp["evidence_status"],
            "matched_terms": comp["matched_terms"],
            "missing_terms": comp["missing_terms"],
            "message": comp["message"]
        })
    return results