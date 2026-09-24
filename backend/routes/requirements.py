
from fastapi import APIRouter
from backend.data.requirements_data import REQUIREMENTS_DATA
from backend.data.detailed_requirements import DETAILED_REQUIREMENTS

router = APIRouter(
    prefix="/requirements",
    tags=["Requirements"]
)


@router.get("/")
def get_requirements():
    return {
        "message": "Requirements API is working!",
        "products_count": len(REQUIREMENTS_DATA),
        "products": REQUIREMENTS_DATA
    }


@router.get("/{product_id}")
def get_product_requirements(product_id: str):

    for product in REQUIREMENTS_DATA:

        if product["product_id"].lower() == product_id.lower():

            return {
                "product": product,
                "requirements_status": "Not yet available",
                "requirements": [],
                "message": (
                    "Verified requirements have not been added "
                    "for this product yet."
                )
            }

    return {
        "product": None,
        "requirements_status": "Not available",
        "requirements": [],
        "message": "Product ID not found."
    }
@router.get("/by-standard/{standard_id}")
def get_requirements_by_standard(standard_id: int):

    if standard_id == DETAILED_REQUIREMENTS["standard_id"]:

        return {
            "standard_id": DETAILED_REQUIREMENTS["standard_id"],
            "standard_number": DETAILED_REQUIREMENTS["standard_number"],
            "product_id": DETAILED_REQUIREMENTS["product_id"],
            "product_name": DETAILED_REQUIREMENTS["product_name"],
            "title": DETAILED_REQUIREMENTS["title"],
            "edition_year": DETAILED_REQUIREMENTS["edition_year"],
            "requirements_status": (
                DETAILED_REQUIREMENTS["requirements_status"]
            ),
            "requirements": DETAILED_REQUIREMENTS["requirements"]
        }

    return {
        "standard_id": standard_id,
        "requirements_status": "Not available",
        "requirements": [],
        "message": "Requirements for this standard were not found."
    }