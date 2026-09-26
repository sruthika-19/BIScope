import unittest
import sys
import os
from fastapi.testclient import TestClient

# Add the parent directory (backend) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

class TestTerminologyAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_1_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "BIScope API"})

    def test_2_supported_product(self):
        response = self.client.post("/api/v1/terminology/analyze", json={"query": "LPG gas stove"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "supported")
        self.assertEqual(len(data["products"]), 1)
        self.assertEqual(data["products"][0]["product_id"], "P004")

    def test_3_clarification(self):
        response = self.client.post("/api/v1/terminology/analyze", json={"query": "water heater"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "needs_clarification")
        self.assertTrue(data["clarification"]["needed"])

    def test_4_multiple_products(self):
        response = self.client.post("/api/v1/terminology/analyze", json={"query": "LPG gas stove and CNG valve"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "multiple_products")
        product_ids = [p["product_id"] for p in data["products"]]
        self.assertIn("P004", product_ids)
        self.assertIn("P010", product_ids)
        
        # Verify isolation of attributes
        p004 = next(p for p in data["products"] if p["product_id"] == "P004")
        p010 = next(p for p in data["products"] if p["product_id"] == "P010")
        self.assertIn("lpg", p004["extracted_attributes"].get("fuel type", []))
        self.assertIn("cng", p010["extracted_attributes"].get("gas type", []))

    def test_5_conflict(self):
        response = self.client.post("/api/v1/terminology/analyze", json={"query": "LPG CNG valve"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "needs_clarification")
        self.assertTrue(data["clarification"]["needed"])

    def test_6_unsupported_product(self):
        response = self.client.post("/api/v1/terminology/analyze", json={"query": "smartphone"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unsupported")

    def test_7_empty_query(self):
        response = self.client.post("/api/v1/terminology/analyze", json={"query": ""})
        self.assertEqual(response.status_code, 422)

    def test_8_missing_query(self):
        response = self.client.post("/api/v1/terminology/analyze", json={})
        self.assertEqual(response.status_code, 422)

    def test_9_whitespace_query(self):
        response = self.client.post("/api/v1/terminology/analyze", json={"query": "   "})
        self.assertEqual(response.status_code, 422)

    def test_10_documentation(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["info"]["title"], "BIScope API")
        self.assertIn("/api/v1/terminology/analyze", data["paths"])

    # --- NEW API VALIDATION EDGE CASES ---

    def test_11_query_too_long(self):
        # Exceeds the max_length=500 constraint defined in our Pydantic schema
        long_query = "a" * 501
        response = self.client.post("/api/v1/terminology/analyze", json={"query": long_query})
        self.assertEqual(response.status_code, 422)
        self.assertIn("String should have at most 500 characters", response.text)

    def test_12_malformed_request(self):
        # Testing a JSON body that sends the wrong key entirely (e.g., 'search_text' instead of 'query')
        response = self.client.post("/api/v1/terminology/analyze", json={"search_text": "geyser"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("Field required", response.text)
if __name__ == '__main__':
    unittest.main()