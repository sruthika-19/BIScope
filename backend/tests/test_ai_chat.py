import unittest
import os
import sys
from unittest.mock import patch, MagicMock

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from services.ai_chat import chat_with_ai

class TestAIChat(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('services.ai_chat.get_groq_client')
    def test_basic_chat_unsupported(self, mock_get_client):
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="I cannot identify this product."))]
        mock_groq.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_groq

        response = self.client.post("/api/v1/chat", json={
            "message": "smartphone",
            "conversation_history": []
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["terminology"]["status"], "unsupported")

    @patch('services.ai_chat.get_groq_client')
    def test_clarification_flow(self, mock_get_client):
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Do you mean a storage water heater or an instant water heater?"))]
        mock_groq.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_groq

        response = self.client.post("/api/v1/chat", json={
            "message": "water heater",
            "conversation_history": []
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["terminology"]["status"], "needs_clarification")

    @patch('services.ai_chat.get_groq_client')
    def test_follow_up_memory(self, mock_get_client):
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="DEVELOPMENT MOCK DATA: No verified BIS standard available yet."))]
        mock_groq.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_groq

        response = self.client.post("/api/v1/chat", json={
            "message": "storage",
            "conversation_history": [
                {"role": "user", "content": "I need a standard for a geyser."},
                {"role": "assistant", "content": "Do you mean a storage water heater or an instant water heater?"}
            ]
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Proves memory worked! It combined "geyser" and "storage"
        self.assertEqual(data["terminology"]["status"], "supported")
        self.assertEqual(data["data_status"], "DATABASE")
        self.assertEqual(data["terminology"]["products"][0]["product_id"], "P007")

    @patch("services.ai_chat.search_standards")
    @patch("services.ai_chat.analyze_query")
    @patch("services.ai_chat.get_groq_client")
    def test_biscope_overview_uses_context_without_calling_provider(
        self, mock_get_client, mock_analyze, mock_search
    ):
        mock_analyze.return_value = {
            "status": "supported",
            "products": [{"product_id": "P001", "normalized_term": "Packaged Drinking Water"}],
            "clarification": {},
        }
        mock_search.return_value = {"status": "DATABASE", "data": {"standards": []}}

        prompt = (
            "User question: Tell me about BIScope\n\n"
            "BIScope context:\n"
            "Product: Packaged Drinking Water (P001); terminology status: supported.\n"
            "Currently selected candidate standard: IS 14543:2024; status: To be verified.\n"
            "Standard record lifecycle: 2016 is an earlier edition; IS 14543:2024 is current.\n"
            "Detailed requirements: 7 records for P001 / IS 14543:2024. "
            "REQ001 General product requirements; REQ002 Microbiological requirements."
        )

        response = chat_with_ai(prompt)

        self.assertIn("AI-powered assistant for Indian Standards", response["reply"])
        self.assertIn("supporting evidence", response["reply"])
        self.assertNotIn("Packaged Drinking Water", response["reply"])
        self.assertNotIn("IS 14543:2024", response["reply"])
        self.assertNotIn("unavailable in the current BIScope context", response["reply"])
        self.assertEqual(response["data_status"], "APPLICATION_INFO")
        self.assertFalse(response["clarification"]["needed"])
        mock_analyze.assert_not_called()
        mock_search.assert_not_called()
        mock_get_client.assert_not_called()

    @patch("services.ai_chat.search_standards")
    @patch("services.ai_chat.analyze_query")
    @patch("services.ai_chat.get_groq_client")
    def test_biscope_general_question_variants_bypass_product_and_provider_lookups(
        self, mock_get_client, mock_analyze, mock_search
    ):
        questions = (
            "Tell me about BIScope",
            "What is BIScope?",
            "What can you do?",
            "How does BIScope work?",
            "What are the features of BIScope?",
            "What is BIS?",
        )
        for question in questions:
            with self.subTest(question=question):
                result = chat_with_ai(
                    f"User question: {question}\n\n"
                    "BIScope context:\nProduct: Industrial Safety Helmet (P011).\n"
                    "Currently selected candidate standard: IS 2925."
                )
                if question == "What is BIS?":
                    self.assertIn("Bureau of Indian Standards", result["reply"])
                else:
                    self.assertIn("BIScope is an AI-powered assistant", result["reply"])
                self.assertNotIn("Industrial Safety Helmet", result["reply"])
                self.assertNotIn("IS 2925", result["reply"])

        mock_analyze.assert_not_called()
        mock_search.assert_not_called()
        mock_get_client.assert_not_called()

    @patch("services.ai_chat.get_groq_client")
    @patch("services.ai_chat.analyze_query")
    def test_provider_error_returns_context_grounded_reply(self, mock_analyze, mock_get_client):
        mock_analyze.return_value = {
            "status": "unsupported",
            "products": [],
            "clarification": {},
        }
        mock_get_client.return_value.chat.completions.create.side_effect = TimeoutError()

        response = chat_with_ai(
            "User question: Tell me about this product\n\n"
            "BIScope context:\n"
            "Product: Packaged Drinking Water (P001).\n"
            "Currently selected candidate standard: IS 14543:2024; status: To be verified."
        )

        self.assertIn("Based on the available BIScope data", response["reply"])
        self.assertIn("IS 14543:2024", response["reply"])
        self.assertNotIn("DEVELOPMENT MOCK DATA", response["reply"])

    def test_missing_groq_key_graceful_fail(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.post("/api/v1/chat", json={
                "message": "water heater",
                "conversation_history": []
            })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Do you mean", data["reply"])

    @patch('services.ai_chat.search_standards')
    @patch('services.ai_chat.analyze_query')
    @patch('services.ai_chat.get_groq_client')
    def test_generic_frontend_prompt_does_not_trigger_certification_guard(
        self, mock_get_client, mock_analyze, mock_search
    ):
        mock_analyze.return_value = {
            "status": "supported",
            "products": [{
                "product_id": "P001",
                "extracted_attributes": {},
            }],
            "clarification": {},
        }
        mock_search.return_value = {
            "status": "DATABASE",
            "data": {"standards": []},
        }
        prompt = (
            "Answer concisely. Do not invent certification requirements.\n\n"
            "User question: Tell me about BIScope\n\n"
            "BIScope context:\nProduct: Packaged Drinking Water (P001)"
        )
        response = chat_with_ai(prompt)

        self.assertIn("BIScope is an AI-powered assistant", response["reply"])
        mock_get_client.assert_not_called()

    @patch('services.ai_chat.search_standards')
    @patch('services.ai_chat.analyze_query')
    @patch('services.ai_chat.get_groq_client')
    def test_frontend_certification_question_still_uses_safety_guard(
        self, mock_get_client, mock_analyze, mock_search
    ):
        mock_analyze.return_value = {
            "status": "supported",
            "products": [{
                "product_id": "P001",
                "extracted_attributes": {},
            }],
            "clarification": {},
        }
        mock_search.return_value = {
            "status": "DATABASE",
            "data": {"standards": []},
        }

        prompt = (
            "Answer concisely. Do not invent certification requirements.\n\n"
            "User question: What are the certification requirements?\n\n"
            "BIScope context:\nProduct: Packaged Drinking Water (P001)"
        )
        response = chat_with_ai(prompt)

        self.assertIn("detailed certification requirements are currently unavailable", response["reply"])
        mock_get_client.assert_not_called()
        
if __name__ == '__main__':
    unittest.main()
