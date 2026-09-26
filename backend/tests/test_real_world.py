import unittest
import sys
import os

# Ensure the backend directory is in the path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.terminology import analyze_query

class TestRealWorldChaos(unittest.TestCase):
    
    def test_1_conversational_noise(self):
        # Tests if the engine can dig through massive amounts of conversational filler
        query = "Hey there! My boss asked me to find out if we need a mandatory ISI mark or BIS certification for a portable LPG burner used in our commercial kitchen. Can you help?"
        res = analyze_query(query)
        self.assertEqual(res["status"], "supported")
        self.assertEqual(res["products"][0]["product_id"], "P004")
        # Proves it successfully extracted "lpg" despite the noise
        self.assertIn("lpg", res["products"][0]["extracted_attributes"].get("fuel type", []))
        
    def test_2_hinglish_mix(self):
        # Tests if regional/unrecognized words break the engine, provided the core English term is present
        query = "Sir, building construction ke liye TMT rebars ka kya standard hai?"
        res = analyze_query(query)
        self.assertEqual(res["status"], "supported")
        self.assertEqual(res["products"][0]["product_id"], "P015")
        
    def test_3_procurement_jargon(self):
        # Tests heavy industrial/tender text common in B2B queries
        query = "Tender Spec: Supply of 11kV distribution transformer with copper winding, oil cooled, 500kVA."
        res = analyze_query(query)
        self.assertEqual(res["status"], "supported")
        self.assertEqual(res["products"][0]["product_id"], "P014")
        self.assertIn("distribution", res["products"][0]["extracted_attributes"].get("transformer type", []))
        
    def test_4_multi_product_extreme(self):
        # Tests 3 completely unrelated products in one messy sentence
        query = "We are setting up a factory. We need to buy ordinary portland cement, industrial safety helmets for the workers, and some ceiling fans."
        res = analyze_query(query)
        self.assertEqual(res["status"], "multiple_products")
        ids = [p["product_id"] for p in res["products"]]
        self.assertIn("P016", ids) # Cement
        self.assertIn("P003", ids) # Helmet
        self.assertIn("P012", ids) # Fan
        
    def test_5_contradiction_in_paragraph(self):
        # Tests if a contradiction works even when buried at the very end of a paragraph
        query = "I am looking for a water pump. It needs to be very powerful, capable of lifting water from 100 feet deep. It will be powered by a diesel engine."
        res = analyze_query(query)
        # Because "diesel" contradicts the solar water pump (P017), it must safely reject it
        self.assertEqual(res["status"], "unsupported")
        
    def test_6_gibberish_and_special_chars(self):
        # Tests if the engine crashes on raw noise or malicious input
        query = "@#$%%^&*()_+)_)!@# asdasdasd qwerty"
        res = analyze_query(query)
        self.assertEqual(res["status"], "unsupported")

if __name__ == '__main__':
    unittest.main()