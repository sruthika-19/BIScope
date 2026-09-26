import shutil
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException, UploadFile, File, Form
from api.schemas import (
    TerminologyAnalyzeRequest, TerminologyAnalyzeResponse,
    ChatRequest, ChatResponse, SearchResponse,
    StandardDetailResponse, ExplanationResponse, AlternativeResponse,
    RequirementItem, RequirementsResponse, ProductRequirementResponse,
    DetailedRequirementsResponse, EvidenceUploadResponse
)
from services.document_extractor import extract_text_from_file
from services.detailed_requirements import get_detailed_requirements
from services.requirements import get_all_requirements, get_requirements_by_product
from services.terminology import analyze_query
from services.ai_chat import chat_with_ai
from services.standard_search import search_database, get_standard_details, build_standard_explanation, build_alternative_explanation
from services.evidence_mapping import map_document_to_requirements
from data.detailed_requirements import DETAILED_REQUIREMENTS
from api.schemas import EvidenceAnalysisResponse

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

@router.post("/terminology/analyze", response_model=TerminologyAnalyzeResponse)
def analyze_terminology(request: TerminologyAnalyzeRequest):
    # Pass the validated query to the existing deterministic terminology engine
    result = analyze_query(request.query)
    return result

# Add ChatRequest and ChatResponse to your existing schemas import
from api.schemas import TerminologyAnalyzeRequest, TerminologyAnalyzeResponse, ChatRequest, ChatResponse
from services.ai_chat import chat_with_ai

# ... existing analyze_terminology route ...

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    # Convert Pydantic objects to dicts for the service layer
    history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
    result = chat_with_ai(request.message, history)
    return result

# Add the new Search endpoint
@router.get("/search", response_model=SearchResponse)
def search_endpoint(query: str = Query(..., min_length=1)):
    results = search_database(query)
    return {
        "query": query,
        "results": results
    }

@router.get("/standards/{standard_id}", response_model=StandardDetailResponse)
def get_standard_endpoint(standard_id: int):
    result = get_standard_details(standard_id)
    if not result:
        raise HTTPException(status_code=404, detail="Standard not found")
    return result

@router.get("/standards/{standard_id}/explanation", response_model=ExplanationResponse)
def get_standard_explanation_endpoint(standard_id: int, product_id: str = Query(..., description="The Product Code (e.g., P003)")):
    result = build_standard_explanation(product_id, standard_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product or Standard not found in the database.")
    return result

@router.get("/standards/{standard_id}/alternatives", response_model=AlternativeResponse)
def get_standard_alternatives_endpoint(standard_id: int, product_id: str = Query(..., description="The Product Code (e.g., P003)")):
    result = build_alternative_explanation(product_id, standard_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found in the database.")
    return result

@router.get("/requirements", response_model=RequirementsResponse)
def get_all_requirements_endpoint():
    requirements = get_all_requirements()
    return {"requirements": requirements}

@router.get("/requirements/{product_id}", response_model=ProductRequirementResponse)
def get_product_requirements_endpoint(product_id: str):
    result = get_requirements_by_product(product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Requirements not found for product")
    return result

@router.get(
    "/requirements/{product_id}/detailed",
    response_model=DetailedRequirementsResponse
)
def get_detailed_requirements_endpoint(product_id: str):
    result = get_detailed_requirements(product_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Detailed requirements not found for product"
        )

    return result

@router.post(
    "/evidence/analyze",
    response_model=EvidenceAnalysisResponse
)
def analyze_evidence(product_id: str, document_text: str):
    if product_id.upper() != DETAILED_REQUIREMENTS["product_id"].upper():
        raise HTTPException(
            status_code=404,
            detail="Evidence mapping is currently available for P001 only"
        )

    results = map_document_to_requirements(
        DETAILED_REQUIREMENTS["requirements"],
        document_text
    )

    return {
        "product_id": product_id.upper(),
        "results": results
    }

@router.post("/evidence/upload", response_model=EvidenceUploadResponse)
def upload_evidence_endpoint(
    product_id: str = Form(..., description="The Product Code (e.g., P001)"),
    file: UploadFile = File(...)
):
    # 1. Validate Extension
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")

    # 2. Save File Temporarily
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # 3. Extract Text
    try:
        extracted_text = extract_text_from_file(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Text extraction failed: {e}")

    # 4. Check for readable text
    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="Document contains no readable text. Scanned or image-only documents require OCR, which is currently not supported."
        )

    # 5. Fetch Requirements
    product_id = product_id.strip().upper()
    detailed_data = get_detailed_requirements(product_id)
    if not detailed_data or "requirements" not in detailed_data:
        raise HTTPException(status_code=404, detail=f"Detailed requirements not found for product {product_id}")

    requirements_list = detailed_data["requirements"]

    # 6. Map Evidence deterministically
    mapping_results = map_document_to_requirements(requirements_list, extracted_text)

    return {
        "product_id": product_id,
        "filename": file.filename,
        "extracted_text_length": len(extracted_text),
        "results": mapping_results
    }