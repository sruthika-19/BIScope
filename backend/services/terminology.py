import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from data.terminology_data import PRODUCTS, STOP_PHRASES, TYPO_MAP, AMBIGUOUS_TERMS, ProductRecord

@dataclass
class Clarification:
    needed: bool
    question: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self):
        if not self.needed:
            return {"needed": False, "question": None, "reason": None}
        return asdict(self)

def normalize_query(query: str) -> str:
    if not query or not query.strip():
        return ""
    q = query.lower().strip()
    q = re.sub(r'[^a-z0-9\s\-\/]', ' ', q)
    for phrase in STOP_PHRASES:
        pattern = rf'\b{re.escape(phrase.strip())}\b'
        q = re.sub(pattern, ' ', q)
    q = " ".join(q.split())
    
    words = q.split()
    normalized_words = [TYPO_MAP.get(word, word) for word in words]
    q = " ".join(normalized_words)
    return q

def get_product_triggers(cleaned_query: str) -> List[Dict]:
    triggers = []
    for product in PRODUCTS:
        terms = set([product.normalized_term.lower()] + product.synonyms + product.keywords + product.descriptive_phrases)
        for term in terms:
            if not term: continue
            for m in re.finditer(rf'\b{re.escape(term.lower())}s?\b', cleaned_query):
                triggers.append({
                    'product_id': product.id,
                    'start': m.start(),
                    'end': m.end()
                })
    return triggers

def get_closest_product_id(attr_start: int, attr_end: int, triggers: List[Dict]) -> Optional[str]:
    if not triggers:
        return None
    min_dist = float('inf')
    closest_pid = None
    for pt in triggers:
        if attr_end <= pt['start']:
            dist = pt['start'] - attr_end
        elif pt['end'] <= attr_start:
            dist = attr_start - pt['end']
        else:
            dist = 0
        
        if dist < min_dist:
            min_dist = dist
            closest_pid = pt['product_id']
    return closest_pid

def extract_attributes(query: str, product: ProductRecord, triggers: List[Dict]) -> Tuple[Dict[str, List[str]], List[str]]:
    extracted = {}
    conflicts = []
    
    for attr, value_map in product.attribute_extractors.items():
        found_values = set()
        for standardized_val, trig_words in value_map.items():
            for t in trig_words:
                for m in re.finditer(rf'\b{re.escape(t)}\b', query):
                    closest_pid = get_closest_product_id(m.start(), m.end(), triggers)
                    if closest_pid == product.id or closest_pid is None:
                        found_values.add(standardized_val)
        if found_values:
            extracted[attr] = list(found_values)
            if len(found_values) > 1:
                conflicts.append(attr)
                
    return extracted, conflicts

def calculate_confidence(match_type: str, has_ambiguous_term: bool, 
                         extracted_count: int, missing_critical_count: int, has_conflict: bool) -> float:
    base = 0.90 if match_type == 'exact' else \
           0.85 if match_type == 'synonym' else \
           0.75 if match_type == 'keyword' else 0.60
           
    score = base
    score += (extracted_count * 0.05)
    
    if has_ambiguous_term:
        score -= 0.20
    if missing_critical_count > 0:
        score -= (missing_critical_count * 0.15)
    if has_conflict:
        score -= 0.30
        
    return max(0.0, min(1.0, round(score, 2)))

def determine_clarification(product: ProductRecord, extracted: dict, conflicts: list, 
                            missing_critical: list, confidence: float, is_multiple: bool) -> Clarification:
    prefix = f"For the {product.normalized_term}: " if is_multiple else ""

    if conflicts:
        attr = conflicts[0]
        vals = " and ".join(sorted(extracted[attr]))
        return Clarification(
            needed=True, 
            question=f"{prefix}You mentioned both {vals}. Which one applies?", 
            reason=f"Conflicting information detected for {attr}."
        )

    if missing_critical:
        attr = missing_critical[0]
        if attr in product.clarification_questions:
            return Clarification(
                needed=True,
                question=f"{prefix}{product.clarification_questions[attr]}",
                reason=f"Missing critical specification: {attr} is required to determine the correct standard."
            )

    if confidence < 0.60:
        return Clarification(
            needed=True,
            question=f"{prefix}Could you provide more specific details or the intended use?",
            reason="The product match confidence is very low due to ambiguous or missing information."
        )

    return Clarification(needed=False)

def analyze_query(query: str) -> Dict[str, Any]:
    cleaned_query = normalize_query(query)
    
    if not cleaned_query:
        return _build_response("unsupported", [], query, Clarification(
            needed=True, question="I couldn't confidently identify the product. Could you provide a product name?", reason="Empty or unrecognized query."
        ))

    candidates = []
    has_ambiguous_direct = any(re.search(rf'\b{ambig}\b', cleaned_query) for ambig in AMBIGUOUS_TERMS)
    
    triggers = get_product_triggers(cleaned_query)

    for product in PRODUCTS:
        match_type = None
        if re.search(rf'\b{re.escape(product.normalized_term.lower())}s?\b', cleaned_query):
            match_type = 'exact'
        elif any(re.search(rf'\b{re.escape(syn.lower())}s?\b', cleaned_query) for syn in product.synonyms):
            match_type = 'synonym'
        elif any(re.search(rf'\b{re.escape(kw.lower())}s?\b', cleaned_query) for kw in product.keywords):
            match_type = 'keyword'
        elif any(desc.lower() in cleaned_query for desc in product.descriptive_phrases):
            match_type = 'descriptive'

        if match_type:
            ext_attrs, conflicts = extract_attributes(cleaned_query, product, triggers)
            
            is_contradictory = False
            for attr, vals in ext_attrs.items():
                if attr in product.contradictory_attributes:
                    if any(v in product.contradictory_attributes[attr] for v in vals):
                        is_contradictory = True
                        break
            if is_contradictory:
                continue
                
            missing_crit = [a for a in product.critical_attributes if a not in ext_attrs]
            is_ambig_penalty = has_ambiguous_direct and len(ext_attrs) == 0
            
            conf = calculate_confidence(match_type, is_ambig_penalty, len(ext_attrs), len(missing_crit), len(conflicts) > 0)
            
            if conf >= 0.40:
                candidates.append({
                    "product": product,
                    "extracted_attributes": ext_attrs,
                    "missing_critical_attributes": missing_crit,
                    "conflicts": conflicts,
                    "heuristic_confidence": conf
                })

    candidates.sort(key=lambda x: x["heuristic_confidence"], reverse=True)

    if not candidates:
        return _build_response("unsupported", [], query, Clarification(
            needed=True, question="This product variant is not currently covered by the supported product list or could not be confidently identified.", reason="No valid product matches found or attributes were explicitly contradictory."
        ))

    distinct_candidates = []
    for cand in candidates:
        is_subsumed = False
        for chosen in distinct_candidates:
            if cand['product'].id == chosen['product'].id:
                is_subsumed = True
                break
        if not is_subsumed:
            distinct_candidates.append(cand)

    is_multiple = len(distinct_candidates) > 1
    
    clarification = Clarification(needed=False)
    for cand in distinct_candidates:
        clar = determine_clarification(
            cand["product"], cand["extracted_attributes"], 
            cand["conflicts"], cand["missing_critical_attributes"], cand["heuristic_confidence"], is_multiple
        )
        if clar.needed:
            clarification = clar
            break

    if is_multiple:
        status = "multiple_products"
    elif clarification.needed:
        status = "needs_clarification"
    else:
        status = "supported"

    return _build_response(status, distinct_candidates, query, clarification)

def _build_response(status: str, candidates: list, query: str, clarification: Clarification) -> Dict[str, Any]:
    products_response = []
    
    for c in candidates:
        products_response.append({
            "product_id": c["product"].id,
            "normalized_term": c["product"].normalized_term,
            "extracted_attributes": c["extracted_attributes"],
            "missing_critical_attributes": c["missing_critical_attributes"],
            "heuristic_confidence": c["heuristic_confidence"]
        })

    return {
        "status": status,
        "products": products_response,
        "normalized_query": normalize_query(query),
        "clarification": clarification.to_dict()
    }