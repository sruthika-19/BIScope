import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class TestEvidenceUploadSecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_filename_cannot_escape_upload_directory(self):
        with TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "uploads"
            upload_dir.mkdir()

            traversal_name = "../outside.txt"

            with patch("api.routes.UPLOAD_DIR", upload_dir):
                response = self.client.post(
                    "/api/v1/evidence/upload",
                    data={"product_id": "P001"},
                    files={
                        "file": (
                            traversal_name,
                            b"Product specification for packaged drinking water.",
                            "text/plain",
                        )
                    },
                )

            self.assertNotEqual(response.status_code, 500)

            escaped_path = upload_dir.parent / "outside.txt"
            self.assertFalse(escaped_path.exists())


if __name__ == "__main__":
    unittest.main()
