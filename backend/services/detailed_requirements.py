from typing import Optional, Dict, Any
from data.detailed_requirements import DETAILED_REQUIREMENTS


def get_detailed_requirements(product_id: str) -> Optional[Dict[str, Any]]:
    if DETAILED_REQUIREMENTS["product_id"].upper() == product_id.upper():
        return DETAILED_REQUIREMENTS
    return None