import json
import os

def load_derived_standards():
    """Dynamically derives standard records from the JSON source of truth."""
    json_path = os.path.join(os.path.dirname(__file__), 'detailed_requirements.json')
    standards_map = {}
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for product, details in data.items():
                standards_map[product] = details.get("standard", "UNKNOWN")
    except Exception:
        pass
    return standards_map

STANDARDS_DATA = load_derived_standards()