import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class TestEvidenceUploadFilenameHandling(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_duplicate_filenames_do_not_overwrite(self):
        with TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "uploads"
            upload_dir.mkdir()

            with patch("api.routes.UPLOAD_DIR", upload_dir):
                first = self.client.post(
                    "/api/v1/evidence/upload",
                    data={"product_id": "P001"},
                    files={
                        "file": (
                            "report.txt",
                            b"First document",
                            "text/plain",
                        )
                    },
                )

                second = self.client.post(
                    "/api/v1/evidence/upload",
                    data={"product_id": "P001"},
                    files={
                        "file": (
                            "report.txt",
                            b"Second document",
                            "text/plain",
                        )
                    },
                )

            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)

            saved_files = list(upload_dir.iterdir())
            self.assertEqual(len(saved_files), 2)


if __name__ == "__main__":
    unittest.main()
