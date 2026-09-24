from fastapi import APIRouter
from backend.data.standards_data import STANDARDS_DATA

router = APIRouter(
    prefix="/api/standards",
    tags=["Standard Details"]
)


@router.get("/{standard_id}")
def get_standard_details(standard_id: int):

    for standard in STANDARDS_DATA:
        if standard["standard_id"] == standard_id:
            return standard

    return {
        "message": "Standard not found",
        "standard_id": standard_id
    }