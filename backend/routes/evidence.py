
from typing import Optional

from fastapi import APIRouter
from backend.services.evidence_mapping import review_evidence

router = APIRouter(
    prefix="/api/evidence",
    tags=["Evidence Mapping"]
)


@router.post("/review")
def review_evidence_api(
    required_evidence: str,
    submitted_evidence: Optional[str] = None
):
    result = review_evidence(
        required_evidence,
        submitted_evidence or ""
    )

    return result