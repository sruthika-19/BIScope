import unittest
import os
import sys
from unittest.mock import patch, MagicMock

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app

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

    def test_missing_groq_key_graceful_fail(self):
        # Temporarily ensure GROQ_API_KEY is not set
        if "GROQ_API_KEY" in os.environ:
            del os.environ["GROQ_API_KEY"]
            
        response = self.client.post("/api/v1/chat", json={
            "message": "water heater",
            "conversation_history": []
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Do you mean", data["reply"]) # Should use graceful fallback
        
if __name__ == '__main__':
    unittest.main()
