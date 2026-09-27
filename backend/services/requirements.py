from typing import Optional, Dict, Any, List
from data.detailed_requirements import DETAILED_REQUIREMENTS_METADATA


def _to_summary(product_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "product_id": metadata["product_id"],
        "product_name": metadata["product_name"],
        "candidate_is_number": metadata["standard_number"],
        "status": metadata["requirements_status"],
    }


def get_all_requirements() -> List[Dict[str, Any]]:
    return [
        _to_summary(product_id, metadata)
        for product_id, metadata in DETAILED_REQUIREMENTS_METADATA.items()
    ]


def get_requirements_by_product(product_id: str) -> Optional[Dict[str, Any]]:
    normalized_product_id = product_id.strip().upper()
    metadata = DETAILED_REQUIREMENTS_METADATA.get(normalized_product_id)

    if not metadata:
        return None

    return _to_summary(normalized_product_id, metadata)