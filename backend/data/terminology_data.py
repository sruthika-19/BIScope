from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ProductRecord:
    id: str
    normalized_term: str
    synonyms: List[str]
    attributes: List[str]
    critical_attributes: List[str] = field(default_factory=list)
    attribute_extractors: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    clarification_questions: Dict[str, str] = field(default_factory=dict)
    contradictory_attributes: Dict[str, List[str]] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    descriptive_phrases: List[str] = field(default_factory=list)

PRODUCTS: List[ProductRecord] = [
    ProductRecord(
        id="P001",
        normalized_term="Packaged Drinking Water",
        synonyms=["bottled water", "packaged water", "drinking water", "drinking water bottle", "bottled drinking water", "packaged drinking water", "drinking water pouch"],
        keywords=["drinking water", "mineral water", "bottled", "water bottle"],
        attributes=["packaging type", "capacity/volume", "still or carbonated", "intended use", "treatment/process type"],
        critical_attributes=["water packaging"],
        attribute_extractors={
            "water packaging": {
                "packaged": ["packaged", "mineral", "sealed", "bottled water"],
                "reusable": ["steel", "copper", "thermos", "flask", "reusable"]
            }
        },
        clarification_questions={
            "water packaging": "Are you referring to commercially packaged/mineral drinking water, or a reusable water bottle?"
        },
        contradictory_attributes={
            "water packaging": ["reusable"]
        }
    ),
    ProductRecord(
        id="P002",
        normalized_term="Sandals and Slippers",
        synonyms=["sandals", "slippers", "rubber slippers", "bathroom slippers", "house slippers", "flip-flops", "chappals", "footwear slippers"],
        keywords=["footwear", "sandal", "slipper", "chappal", "flip flop"],
        attributes=["material", "intended use", "sole material", "construction type", "adult/children", "footwear type"],
        critical_attributes=["footwear type"],
        attribute_extractors={
            "footwear type": {
                "open": ["sandal", "slipper", "chappals", "chappal", "flip-flop"],
                "closed": ["shoe", "sneaker", "boot", "heels"]
            }
        },
        contradictory_attributes={
            "footwear type": ["closed"]
        }
    ),
    ProductRecord(
        id="P003",
        normalized_term="Industrial Safety Helmet",
        synonyms=["industrial safety helmet", "industrial helmet", "hard hat", "factory helmet", "construction helmet", "industrial hard hat"],
        keywords=["safety helmet", "protective helmet", "work helmet", "industrial safety", "hard hat", "helmet"],
        attributes=["intended use", "helmet type", "material", "industrial vs other use", "electrical insulation requirement", "impact protection class"],
        critical_attributes=["intended use"],
        attribute_extractors={
            "intended use": {
                "industrial": ["industrial", "factory", "construction", "work", "workplace"],
                "motorcycle": ["motorcycle", "bike", "riding", "road", "scooter"]
            }
        },
        clarification_questions={
            "intended use": "Is the helmet intended for industrial/workplace use or motorcycle/road use?"
        },
        contradictory_attributes={
            "intended use": ["motorcycle"]
        }
    ),
    ProductRecord(
        id="P004",
        normalized_term="LPG Gas Stove",
        synonyms=["lpg stove", "lpg burner", "lpg gas stove"],
        keywords=["gas stove", "gas cooker", "cooking stove", "stove", "burner", "kitchen gas stove", "domestic gas stove"],
        attributes=["number of burners", "fuel type", "domestic/commercial use", "burner type", "ignition type", "built-in/portable"],
        critical_attributes=["fuel type"],
        attribute_extractors={
            "fuel type": {
                "lpg": ["lpg", "cylinder"],
                "cng": ["cng", "piped"],
                "electric": ["electric", "induction"]
            }
        },
        clarification_questions={
            "fuel type": "Does the stove use LPG, CNG, or another fuel?"
        },
        contradictory_attributes={
            "fuel type": ["cng", "electric"]
        }
    ),
    ProductRecord(
        id="P005",
        normalized_term="PVC Insulated Cable",
        synonyms=["pvc cable", "pvc wire", "pvc insulated wire"],
        keywords=["electric cable", "electrical cable", "insulated cable", "insulated wire", "electrical wire", "power cable", "wire", "cable"],
        descriptive_phrases=["pvc insulated electrical wire"],
        attributes=["number of cores", "conductor material", "conductor size/cross-section", "voltage rating", "flexible/rigid", "application", "insulation/sheath type"],
        critical_attributes=["cable type"],
        attribute_extractors={
            "cable type": {
                "pvc": ["pvc"],
                "flexible": ["flexible"],
                "data": ["hdmi", "lan", "ethernet", "usb", "fiber optic", "data"]
            }
        },
        clarification_questions={
            "cable type": "What type of cable is it—PVC insulated cable, flexible cable, or another type?"
        },
        contradictory_attributes={
            "cable type": ["data"]
        }
    ),
    ProductRecord(
        id="P006",
        normalized_term="RO Water Treatment System",
        synonyms=["ro purifier", "ro system", "reverse osmosis system", "reverse osmosis purifier", "ro water purifier", "ro filter", "reverse osmosis water filter"],
        keywords=["water purifier", "drinking water purifier", "reverse osmosis", "purifier", "filter"],
        attributes=["treatment technology", "capacity", "intended water source", "domestic/commercial use", "purification capacity", "installation type"],
        critical_attributes=["purification technology"],
        attribute_extractors={
            "purification technology": {
                "ro": ["ro", "reverse osmosis"],
                "other": ["gravity", "uv only"]
            }
        },
        clarification_questions={
            "purification technology": "Are you referring to a Reverse Osmosis (RO) water purifier or another purification technology (such as gravity filters)?"
        },
        contradictory_attributes={
            "purification technology": ["other"]
        }
    ),
    ProductRecord(
        id="P007",
        normalized_term="Storage Water Heater",
        synonyms=["geyser", "storage geyser", "storage heater", "electric storage water heater", "storage water heater"],
        keywords=["water heater", "electric water heater", "hot water heater", "storage"],
        descriptive_phrases=["machine that heats water and stores it"],
        attributes=["storage/instant type", "capacity", "electrical rating", "operating pressure", "domestic/commercial use", "installation orientation"],
        critical_attributes=["storage/instant type"],
        attribute_extractors={
            "storage/instant type": {
                "storage": ["storage", "store", "tank", "geyser"],
                "instant": ["instant", "tankless", "immediate", "immersion rod"]
            }
        },
        clarification_questions={
            "storage/instant type": "Do you mean a storage water heater or an instant water heater?"
        },
        contradictory_attributes={
            "storage/instant type": ["instant"]
        }
    ),
    ProductRecord(
        id="P008",
        normalized_term="Paver Blocks",
        synonyms=["paver blocks", "paving blocks", "concrete pavers", "concrete blocks", "interlocking blocks", "interlocking pavers", "paving stones", "concrete paving blocks", "floor pavers"],
        keywords=["paver block", "paving block", "concrete paver", "block"],
        attributes=["material", "shape", "dimensions", "thickness", "intended application", "load/traffic requirement", "surface/finish", "interlocking/non-interlocking"],
        critical_attributes=["block type"],
        attribute_extractors={
            "block type": {
                "paver": ["paver", "paving", "floor", "ground"],
                "wall": ["wall", "red brick", "clay brick", "hollow block"]
            }
        },
        clarification_questions={
            "block type": "Are you referring to concrete paver blocks for flooring, or blocks for wall construction?"
        },
        contradictory_attributes={
            "block type": ["wall"]
        }
    ),
    ProductRecord(
        id="P009",
        normalized_term="Toys",
        synonyms=["children's toys", "kids toys", "children's playthings", "kids' playthings", "baby toys", "children's play products"],
        keywords=["toy", "plaything", "toys", "children", "kids", "play"],
        attributes=["age group", "toy type", "material", "electric/non-electric", "intended use", "battery-operated/non-battery-operated", "size/design"],
        critical_attributes=["intended user"],
        attribute_extractors={
            "intended user": {
                "child": ["child", "kid", "baby", "children"],
                "pet": ["pet", "dog", "cat"]
            }
        },
        clarification_questions={
            "intended user": "Are you referring to children's toys or pet toys?"
        },
        contradictory_attributes={
            "intended user": ["pet"]
        }
    ),
    ProductRecord(
        id="P010",
        normalized_term="LPG/CNG Valves",
        synonyms=["lpg valve", "cng valve", "gas valve", "cylinder valve", "lpg cylinder valve", "cng gas valve", "gas cylinder valve", "fuel gas valve"],
        keywords=["valve", "valves", "pressure", "gas"],
        attributes=["gas type", "valve application", "cylinder/container type", "pressure rating", "connection type", "valve material/design"],
        critical_attributes=["gas type", "valve purpose"],
        attribute_extractors={
            "gas type": {
                "lpg": ["lpg", "liquefied"],
                "cng": ["cng", "compressed"]
            },
            "valve purpose": {
                "gas": ["gas", "cylinder", "lpg", "cng"],
                "liquid": ["water", "plumbing", "liquid"]
            }
        },
        clarification_questions={
            "gas type": "Is the valve for LPG or CNG cylinders?",
            "valve purpose": "Are you referring to a gas cylinder valve or a water/plumbing valve?"
        },
        contradictory_attributes={
            "valve purpose": ["liquid"]
        }
    ),
    ProductRecord(
        id="P011",
        normalized_term="Single-Phase Induction Motor",
        synonyms=["single-phase motor", "single phase induction motor", "single-phase ac motor", "single phase motor"],
        keywords=["induction motor", "ac motor", "electric motor", "induction electric motor", "motor"],
        attributes=["power rating", "voltage", "frequency", "motor type", "enclosure/protection", "speed", "duty/application", "efficiency requirement"],
        critical_attributes=["motor type"],
        attribute_extractors={
            "motor type": {
                "single-phase induction": ["single phase", "single-phase", "1 phase"],
                "other": ["three phase", "three-phase", "3 phase", "dc", "servo", "stepper"]
            }
        },
        clarification_questions={
            "motor type": "Are you referring to a single-phase induction motor or a different type (such as three-phase)?"
        },
        contradictory_attributes={
            "motor type": ["other"]
        }
    ),
    ProductRecord(
        id="P012",
        normalized_term="Electric Ceiling Fan",
        synonyms=["ceiling fan", "electric ceiling fan", "overhead fan", "ceiling-mounted fan", "home ceiling fan"],
        keywords=["fan", "electric fan", "room fan", "domestic fan"],
        attributes=["sweep size", "voltage", "power rating", "speed", "motor type", "domestic/commercial use", "electronic/smart features"],
        critical_attributes=["fan type"],
        attribute_extractors={
            "fan type": {
                "ceiling": ["ceiling", "overhead"],
                "other": ["table", "pedestal", "exhaust", "wall"]
            }
        },
        clarification_questions={
            "fan type": "Are you referring to a ceiling fan, or another type like a table or exhaust fan?"
        },
        contradictory_attributes={
            "fan type": ["other"]
        }
    ),
    ProductRecord(
        id="P013",
        normalized_term="Cattle Feed",
        synonyms=["cattle feed", "dairy feed", "cow feed", "buffalo feed", "compounded cattle feed", "dairy cattle feed"],
        keywords=["animal feed", "livestock feed"],
        attributes=["animal type", "feed type", "age/stage of animal", "purpose", "ingredients/form", "nutritional composition"],
        critical_attributes=["animal type"],
        attribute_extractors={
            "animal type": {
                "cattle": ["cattle", "cow", "buffalo", "dairy"],
                "other": ["poultry", "dog", "cat", "fish", "horse", "bird"]
            }
        },
        clarification_questions={
            "animal type": "Are you referring to cattle feed or feed for another animal?"
        },
        contradictory_attributes={
            "animal type": ["other"]
        }
    ),
    ProductRecord(
        id="P014",
        normalized_term="Distribution Transformer",
        synonyms=["distribution transformer", "distribution power transformer", "11kv transformer", "33kv transformer", "utility transformer"],
        keywords=["electrical transformer", "power transformer", "electric transformer", "transformer"],
        attributes=["rated power", "voltage ratio", "phase", "frequency", "cooling method", "oil/dry type", "installation/application", "insulation type"],
        critical_attributes=["transformer type"],
        attribute_extractors={
            "transformer type": {
                "distribution": ["distribution", "11kv", "33kv"],
                "other": ["instrument", "current", "voltage", "potential", "welding"]
            }
        },
        clarification_questions={
            "transformer type": "Are you referring to a distribution transformer or another type?"
        },
        contradictory_attributes={
            "transformer type": ["other"]
        }
    ),
    ProductRecord(
        id="P015",
        normalized_term="Reinforcement Steel Bars",
        synonyms=["reinforcement bars", "tmt bars", "tmt steel", "rebars", "reinforcement steel", "concrete reinforcement bars", "deformed steel bars", "reinforcement steel bars"],
        keywords=["tmt bar", "rebar", "reinforcement bar", "steel bar", "steel bars", "construction steel"],
        descriptive_phrases=["steel bars used for concrete reinforcement"],
        attributes=["grade", "bar diameter", "manufacturing process", "steel type", "surface", "intended application", "strength requirements"],
        critical_attributes=["bar application"],
        attribute_extractors={
            "bar application": {
                "reinforcement": ["reinforcement", "reinforcing", "tmt", "rebar", "rebars", "concrete", "construction"],
                "other": ["stainless", "structural", "tool", "spring", "pipe", "sheet", "plate"]
            }
        },
        clarification_questions={
            "bar application": "Are you referring to reinforcement steel bars (such as TMT/rebars) for concrete or another type of steel bar?"
        },
        contradictory_attributes={
            "bar application": ["other"]
        }
    ),
    ProductRecord(
        id="P016",
        normalized_term="Cement",
        synonyms=["portland cement", "construction cement", "building cement", "opc cement", "ordinary portland cement", "construction material cement", "opc"],
        keywords=["cement", "portland"],
        attributes=["cement type/grade", "intended application", "composition", "strength class", "ordinary/special-purpose cement", "packaging"],
        critical_attributes=["cement type"],
        attribute_extractors={
            "cement type": {
                "construction": ["construction", "building", "portland", "opc"],
                "other": ["white cement", "putty", "plaster", "dental"]
            }
        },
        contradictory_attributes={
            "cement type": ["other"]
        }
    ),
    ProductRecord(
        id="P017",
        normalized_term="Solar Water Pump",
        synonyms=["solar water pump", "solar pump", "solar-powered pump", "solar powered water pump", "pv water pump", "photovoltaic water pump", "solar irrigation pump", "solar pumping system"],
        keywords=["solar pump", "solar water pump", "water pump", "pump"],
        descriptive_phrases=["solar pump for irrigation"],
        attributes=["pump type", "solar/pv system type", "capacity", "head", "flow rate", "motor type", "ac/dc", "application", "power rating"],
        critical_attributes=["power source"],
        attribute_extractors={
            "power source": {
                "solar": ["solar", "pv", "photovoltaic"],
                "other": ["diesel", "petrol", "hand", "manual"]
            }
        },
        clarification_questions={
            "power source": "Are you referring to a solar-powered water pump or a different type (e.g., diesel or hand pump)?"
        },
        contradictory_attributes={
            "power source": ["other"]
        }
    ),
    ProductRecord(
        id="P018",
        normalized_term="IT Equipment",
        synonyms=[],
        keywords=["electronic office equipment", "it devices", "information technology devices", "computing equipment", "electronic equipment", "computer equipment", "it equipment", "computer hardware", "computer", "laptop", "desktop", "server", "printer", "scanner", "router", "switch", "modem"],
        attributes=["equipment type", "intended use", "power source", "voltage", "device category", "wired/wireless", "rated power", "applicable environmental/safety characteristics"],
        critical_attributes=["equipment category"],
        attribute_extractors={
            "equipment category": {
                "specific": ["computer", "laptop", "desktop", "server", "printer", "scanner", "router", "switch", "modem", "hardware", "device"],
                "other": ["medical", "industrial", "refrigerator", "home appliance"]
            }
        },
        clarification_questions={
            "equipment category": "What specific type of IT or electronic equipment are you referring to (e.g., computer, printer, router)?"
        },
        contradictory_attributes={
            "equipment category": ["other"]
        }
    )
]

STOP_PHRASES: List[str] = [
    "i need bis certification for a", "i need bis certification for", 
    "i want a bis standard for an", "i need a bis standard for an", "what bis standard applies to an",
    "i want a bis standard for a", "i want a bis standard for",
    "i need a bis standard for a", "i need a bis standard for",
    "what bis standard applies to a", "what bis standard applies to",
    "i need", "i want", "tell me about", "tell me", "information about", 
    "bis standard for", "bis certification for", "standard for", 
    "certification for", "please", "can you", "help me with", "give me the"
]

TYPO_MAP: Dict[str, str] = {
    "geiser": "geyser",
    "cment": "cement",
    "sliper": "slippers",
    "slipers": "slippers",
    "chapal": "chappals",
    "chappal": "chappals",
    "ro water filter": "ro purifier"
}

AMBIGUOUS_TERMS = ["helmet", "cable", "motor", "transformer", "water heater", "valve", "stove", "it equipment", "electronic equipment", "animal feed", "steel bars", "water purifier", "fan", "pump", "cement"]