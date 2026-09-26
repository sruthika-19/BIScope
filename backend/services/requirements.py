from typing import Optional, Dict, Any, List
from data.requirements_data import REQUIREMENTS_DATA

def get_all_requirements() -> List[Dict[str, Any]]:
    return REQUIREMENTS_DATA

def get_requirements_by_product(product_id: str) -> Optional[Dict[str, Any]]:
    for item in REQUIREMENTS_DATA:
        if item["product_id"].upper() == product_id.upper():
            return item
    return None