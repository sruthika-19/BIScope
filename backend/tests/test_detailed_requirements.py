import os
import sys
import unittest

from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.detailed_requirements import DETAILED_REQUIREMENTS
from main import app


EXPECTED_COUNTS = {
    "P001": 7,
    "P002": 7,
    "P003": 9,
    "P004": 5,
    "P005": 4,
    "P006": 12,
    "P007": 4,
    "P008": 8,
    "P009": 4,
    "P010": 4,
    "P011": 7,
    "P012": 4,
    "P013": 4,
    "P014": 5,
    "P015": 9,
    "P016": 7,
    "P017": 5,
    "P018": 12,
}
REQUIREMENT_FIELDS = {
    "requirement_id",
    "standard_id",
    "product_id",
    "requirement_description",
    "clause_reference",
    "limit_or_condition",
    "unit",
    "comparison_type",
    "required_evidence",
    "evidence_type",
    "official_source",
    "verification_status",
    "verification_notes",
}


class TestDetailedRequirementsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_all_products_return_their_exact_requirements(self):
        self.assertEqual(len(DETAILED_REQUIREMENTS), sum(EXPECTED_COUNTS.values()))

        for product_id, expected_count in EXPECTED_COUNTS.items():
            with self.subTest(product_id=product_id):
                source_requirements = [
                    requirement
                    for requirement in DETAILED_REQUIREMENTS
                    if requirement["product_id"] == product_id
                ]
                response = self.client.get(
                    f"/api/v1/requirements/{product_id}/detailed"
                )
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(result["product_id"], product_id)
                self.assertEqual(len(result["requirements"]), expected_count)
                self.assertEqual(
                    result["requirements"],
                    source_requirements,
                )
                self.assertTrue(
                    all(
                        set(requirement) == REQUIREMENT_FIELDS
                        for requirement in result["requirements"]
                    )
                )
                self.assertTrue(
                    all(
                        requirement["product_id"] == product_id
                        and requirement["standard_id"]
                        == f"STD{result['standard_id']:03d}"
                        for requirement in result["requirements"]
                    )
                )

    def test_p003_requirements_are_not_p001_requirements(self):
        p001 = self.client.get("/api/v1/requirements/P001/detailed").json()
        p003 = self.client.get("/api/v1/requirements/P003/detailed").json()
        self.assertEqual(
            [item["requirement_id"] for item in p003["requirements"]],
            [f"REQ{i:03d}" for i in range(15, 24)],
        )
        self.assertNotEqual(p003["requirements"], p001["requirements"])

    def test_lookup_normalizes_product_id_and_returns_404_for_unknown_product(self):
        self.assertEqual(
            self.client.get("/api/v1/requirements/ p003 /detailed").status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/v1/requirements/P999/detailed").status_code,
            404,
        )

    def test_evidence_analysis_uses_selected_product_requirements_and_context(self):
        response = self.client.post(
            "/api/v1/evidence/analyze",
            params={"product_id": "p003", "document_text": "Clause 3.1 shell"},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(
            [result["requirement_id"] for result in results],
            [f"REQ{i:03d}" for i in range(15, 24)],
        )
        self.assertIn("shell", results[0]["matched_terms"])


if __name__ == "__main__":
    unittest.main()
