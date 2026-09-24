
from fastapi import APIRouter
from backend.data.requirements_data import REQUIREMENTS_DATA
from backend.data.standards_data import PRODUCT_STANDARD_MAP

router = APIRouter(
    prefix="/api",
    tags=["Product Search"]
)


@router.get("/search")
def search_products(query: str):

    results = []

    for product in REQUIREMENTS_DATA:

        product_name = product["product_name"].lower()
        candidate_is = product["candidate_is_number"].lower()

        if (
            query.lower() in product_name
            or query.lower() in candidate_is
        ):

            result = {
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "search_terms": None,
                "normalized_term": None,
                "category": None,
                "standard_id": PRODUCT_STANDARD_MAP.get(
                    product["product_id"]
                ),
                "standard_number": product["candidate_is_number"],
                "title": None,
                "scope": None,
                "status": product["status"],
                "source": None
            }

            results.append(result)

    return {
        "query": query,
        "message": (
            "Matching products found"
            if results
            else "No matching products found"
        ),
        "results": results
    }