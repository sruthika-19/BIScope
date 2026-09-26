from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional

class TerminologyAnalyzeRequest(BaseModel):
    query: str = Field(..., max_length=500, description="The user's raw input query")

    @field_validator('query')
    @classmethod
    def not_empty_or_whitespace(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty or just whitespace")
        return v

class ClarificationSchema(BaseModel):
    needed: bool
    question: Optional[str] = None
    reason: Optional[str] = None

class ProductResponseSchema(BaseModel):
    product_id: str
    normalized_term: str
    extracted_attributes: Dict[str, List[str]]
    missing_critical_attributes: List[str]
    heuristic_confidence: float

class TerminologyAnalyzeResponse(BaseModel):
    status: str
    products: List[ProductResponseSchema]
    normalized_query: str
    clarification: ClarificationSchema

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's new message")
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Previous messages")

class ChatResponse(BaseModel):
    reply: str
    terminology: dict
    clarification: dict
    data_status: str
    sources: list

class SearchResultItem(BaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    normalized_term: Optional[str] = None
    standard_id: Optional[int] = None
    standard_number: Optional[str] = None
    title: Optional[str] = None
    edition_year: Optional[str] = None
    status: Optional[str] = None
    qco_info: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

class StandardDetailResponse(BaseModel):
    id: int
    standard_number: Optional[str] = None
    title: Optional[str] = None
    scope: Optional[str] = None
    edition_year: Optional[str] = None
    revision: Optional[str] = None
    newer_edition: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    qco_info: Optional[str] = None

class ExplanationResponse(BaseModel):
    product_id: str
    standard_id: int
    standard_number: str
    relationship: str
    matches: List[str]
    mismatches: List[str]
    unknown: List[str]
    explanation: str

class AlternativeItem(BaseModel):
    standard_id: int
    standard_number: str
    title: str
    relationship: str
    matches: List[str]
    mismatches: List[str]
    unknown: List[str]
    explanation: str

class AlternativeResponse(BaseModel):
    product_id: str
    selected_standard_id: int
    alternatives: List[AlternativeItem]

class RequirementItem(BaseModel):
    product_id: str
    product_name: str
    candidate_is_number: str
    status: str

class RequirementsResponse(BaseModel):
    requirements: List[RequirementItem]

class ProductRequirementResponse(BaseModel):
    product_id: str
    product_name: str
    candidate_is_number: str
    status: str

class DetailedRequirementItem(BaseModel):
    requirement_id: str
    standard_id: str
    product_id: str
    requirement_description: str
    clause_reference: str
    limit_or_condition: str
    unit: Optional[str] = None
    comparison_type: str
    required_evidence: str
    evidence_type: str
    official_source: str
    verification_status: str
    verification_notes: str


class DetailedRequirementsResponse(BaseModel):
    standard_id: int
    standard_number: str
    product_id: str
    product_name: str
    title: str
    edition_year: int
    requirements_status: str
    requirements: List[DetailedRequirementItem]

class EvidenceRequirementResult(BaseModel):
    requirement_id: str
    requirement_description: str
    required_evidence: str
    evidence_type: str
    status: str
    evidence_status: str
    matched_terms: List[str]
    missing_terms: List[str]
    message: str


class EvidenceAnalysisResponse(BaseModel):
    product_id: str
    results: List[EvidenceRequirementResult]

class EvidenceUploadResponse(BaseModel):
    product_id: str
    filename: str
    extracted_text_length: int
    results: List[EvidenceRequirementResult]

