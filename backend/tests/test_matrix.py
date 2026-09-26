import unittest
from services.terminology import analyze_query
from data.terminology_data import PRODUCTS

class TestTerminologyMatrix(unittest.TestCase):
    
    def test_1_all_synonyms(self):
        """Every synonym should successfully route to its parent product."""
        for product in PRODUCTS:
            for synonym in product.synonyms:
                with self.subTest(product=product.id, synonym=synonym):
                    res = analyze_query(synonym)
                    product_ids = [p["product_id"] for p in res.get("products", [])]
                    self.assertIn(product.id, product_ids, f"Synonym '{synonym}' failed to map to {product.id}")

    def test_2_all_valid_extractors(self):
        """Every attribute extractor word should successfully be extracted."""
        for product in PRODUCTS:
            base_term = product.normalized_term 
            for attr_name, value_map in product.attribute_extractors.items():
                for standardized_val, triggers in value_map.items():
                    # Skip if this value is meant to contradict (tested in test 3)
                    if attr_name in product.contradictory_attributes and standardized_val in product.contradictory_attributes[attr_name]:
                        continue
                        
                    for trigger in triggers:
                        query = f"{base_term} {trigger}"
                        with self.subTest(product=product.id, attr=attr_name, trigger=trigger):
                            res = analyze_query(query)
                            
                            # Find the specific product in the results
                            match = next((p for p in res.get("products", []) if p["product_id"] == product.id), None)
                            self.assertIsNotNone(match, f"Query '{query}' failed to map to {product.id}")
                            
                            extracted = match["extracted_attributes"].get(attr_name, [])
                            self.assertIn(standardized_val, extracted, f"Failed to extract '{standardized_val}' using trigger word '{trigger}'")

    def test_3_all_contradictions(self):
        """Every contradiction trigger should successfully reject the product."""
        for product in PRODUCTS:
            base_term = product.normalized_term 
            for attr_name, contradicted_vals in product.contradictory_attributes.items():
                for c_val in contradicted_vals:
                    if attr_name in product.attribute_extractors and c_val in product.attribute_extractors[attr_name]:
                        triggers = product.attribute_extractors[attr_name][c_val]
                        for trigger in triggers:
                            query = f"{base_term} {trigger}"
                            with self.subTest(product=product.id, contradicted_val=c_val, trigger=trigger):
                                res = analyze_query(query)
                                product_ids = [p["product_id"] for p in res.get("products", [])]
                                # The product should NOT be in the results (it should be filtered out)
                                self.assertNotIn(product.id, product_ids, f"Contradiction failed! '{trigger}' should have rejected {product.id} but it survived.")

if __name__ == '__main__':
    unittest.main()