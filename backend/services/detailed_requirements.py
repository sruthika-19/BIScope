from typing import Optional, Dict, Any
from data.detailed_requirements import (
    DETAILED_REQUIREMENTS,
    DETAILED_REQUIREMENTS_METADATA,
)


def get_detailed_requirements(product_id: str) -> Optional[Dict[str, Any]]:
    normalized_product_id = product_id.strip().upper()
    requirements = [
        requirement
        for requirement in DETAILED_REQUIREMENTS
        if requirement["product_id"].upper() == normalized_product_id
    ]
    metadata = DETAILED_REQUIREMENTS_METADATA.get(normalized_product_id)
    if not requirements or not metadata:
        return None
    return {**metadata, "requirements": requirements}