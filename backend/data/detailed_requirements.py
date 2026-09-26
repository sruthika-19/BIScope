import json
from pathlib import Path
from typing import Any, Dict, List


with Path(__file__).with_name("detailed_requirements.json").open(encoding="utf-8") as data_file:
    _requirements_by_product: Dict[str, Dict[str, Any]] = json.load(data_file)

DETAILED_REQUIREMENTS: List[Dict[str, Any]] = [
    requirement
    for product in _requirements_by_product.values()
    for requirement in product["requirements"]
]

DETAILED_REQUIREMENTS_METADATA: Dict[str, Dict[str, Any]] = {
    product_id: {
        key: value
        for key, value in product.items()
        if key != "requirements"
    }
    for product_id, product in _requirements_by_product.items()
}
