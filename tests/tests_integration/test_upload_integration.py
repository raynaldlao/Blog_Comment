import io
import re


class TestFileUpload:
    """End-to-end tests for file upload and retrieval."""

    def test_upload_image_success(self, client):
        data = {"file": (io.BytesIO(b"fake_image_data"), "photo.jpg", "image/jpeg")}
        response = client.post(
            "/api/upload/image",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 201
        body = response.get_json()
        assert body is not None
        assert "url" in body
        assert body["url"].startswith("/uploads/")
        assert body["url"].endswith("/photo.jpg")

    def test_upload_image_missing_file(self, client):
        response = client.post(
            "/api/upload/image",
            data={},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        body = response.get_json()
        assert body is not None
        assert "error" in body

    def test_upload_image_invalid_extension(self, client):
        data = {"file": (io.BytesIO(b"some text"), "notes.txt", "text/plain")}
        response = client.post(
            "/api/upload/image",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        body = response.get_json()
        assert body is not None
        assert "error" in body

    def test_serve_uploaded_file(self, client):
        data = {"file": (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"), "tiny.png", "image/png")}
        upload_resp = client.post(
            "/api/upload/image",
            data=data,
            content_type="multipart/form-data",
        )
        assert upload_resp.status_code == 201
        url = upload_resp.get_json()["url"]
        uuid_match = re.search(r"/uploads/([^/]+)/", url)
        assert uuid_match is not None

        serve_resp = client.get(url)
        assert serve_resp.status_code == 200
        assert serve_resp.mimetype == "image/png"
        assert serve_resp.data == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
