import os
import sys
import unittest
from unittest.mock import patch

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from services.bis_data import search_standards
from services.standard_search import (
    build_alternative_explanation,
    build_standard_explanation,
    get_standard_details,
    search_database,
)


class TestStandardSearchDatabaseSchema(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_search_uses_imported_product_and_standard_columns(self):
        for query, product_id, product_name in (
            ("cement", "P016", "Cement"),
            ("packaged drinking water", "P001", "Packaged Drinking Water"),
        ):
            with self.subTest(query=query):
                results = search_database(query)
                result = next(item for item in results if item["product_id"] == product_id)
                self.assertEqual(result["product_name"], product_name)
                self.assertIsNone(result["normalized_term"])
                self.assertIsNotNone(result["title"])
                self.assertIsNotNone(result["edition_year"])
                self.assertIsNotNone(result["status"])
                self.assertIsNotNone(result["qco_info"])

                response = self.client.get("/api/v1/search", params={"query": query})
                self.assertEqual(response.status_code, 200)
                api_result = next(
                    item for item in response.json()["results"]
                    if item["product_id"] == product_id
                )
                self.assertEqual(api_result["product_name"], product_name)
                self.assertIsNotNone(api_result["title"])

    def test_standard_details_aliases_authoritative_year(self):
        search_result = next(
            item for item in search_database("packaged drinking water")
            if item["product_id"] == "P001"
        )

        details = get_standard_details(search_result["standard_id"])
        self.assertEqual(details["standard_number"], "IS 14543:2024")
        self.assertEqual(details["edition_year"], "2024.0")
        self.assertIsNotNone(details["title"])
        self.assertIsNotNone(details["status"])

        response = self.client.get(f"/api/v1/standards/{search_result['standard_id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["edition_year"], "2024.0")
        self.assertIsNotNone(response.json()["title"])
        self.assertIsNotNone(response.json()["qco_info"])

    def test_standard_explanation_uses_product_name_and_actual_mapping(self):
        search_result = next(
            item for item in search_database("packaged drinking water")
            if item["product_id"] == "P001"
        )
        explanation = build_standard_explanation("P001", search_result["standard_id"])

        self.assertEqual(explanation["relationship"], "candidate")
        self.assertIn("Packaged Drinking Water", explanation["explanation"])

        response = self.client.get(
            f"/api/v1/standards/{search_result['standard_id']}/explanation",
            params={"product_id": "P001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["relationship"], "candidate")

    def test_alternative_explanation_returns_valid_empty_result(self):
        search_result = next(
            item for item in search_database("packaged drinking water")
            if item["product_id"] == "P001"
        )
        result = build_alternative_explanation("P001", search_result["standard_id"])

        self.assertEqual(result["alternatives"], [])
        response = self.client.get(
            f"/api/v1/standards/{search_result['standard_id']}/alternatives",
            params={"product_id": "P001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["alternatives"], [])

    def test_ai_chat_database_lookup_uses_imported_schema(self):
        with patch("services.ai_chat.get_groq_client", return_value=None):
            response = self.client.post(
                "/api/v1/chat",
                json={
                    "message": "Tell me about the requirements for packaged drinking water",
                    "conversation_history": [],
                },
            )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["data_status"], "DATABASE")
        self.assertEqual(result["terminology"]["products"][0]["product_id"], "P001")
        self.assertIn("IS 14543:2024", result["reply"])
        self.assertIn("REQ001", result["reply"])
        self.assertEqual(search_standards("P001", {})["status"], "DATABASE")


    def test_cement_search_does_not_match_reinforcement(self):
        results = search_database("cement")

        product_ids = [item["product_id"] for item in results]

        self.assertIn("P016", product_ids)
        self.assertNotIn("P015", product_ids)

        response = self.client.get(
            "/api/v1/search",
            params={"query": "cement"},
        )

        self.assertEqual(response.status_code, 200)

        api_product_ids = [
            item["product_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(api_product_ids, ["P016"])

    def test_standard_details_rejects_oversized_standard_id(self):
        oversized_id = "999999999999999999999999999999999999999999999999999999999999"

        response = self.client.get(f"/api/v1/standards/{oversized_id}")

        self.assertNotEqual(response.status_code, 500)
        self.assertIn(response.status_code, (400, 404, 422))


if __name__ == "__main__":
    unittest.main()
