from io import BytesIO

from flask import jsonify, request, send_file
from src.application.application_exceptions import FileTooLargeError, FileTypeError
from src.application.input_ports.file_management import FileManagementPort
from src.infrastructure.input_adapters.dto.file_upload_request import FileUploadRequest


class FlaskFileAdapter:
    """Flask input adapter for file upload and retrieval.

    Upload endpoint validates input via FileUploadRequest DTO, delegates to
    FileService, and returns JSON with the serving URL.
    Serve endpoint streams raw bytes from BYTEA storage with correct MIME type.
    """

    def __init__(self, file_service: FileManagementPort):
        self.file_service = file_service

    def upload_image(self):
        """Handle POST /api/upload/image.

        Accepts a multipart file upload, persists via FileService,
        returns JSON with serving URL on success.

        Returns:
            JSON response with upload URL (201) or error message (400).
        """
        uploaded_file = request.files.get("file")
        if uploaded_file is None or not uploaded_file.filename:
            return jsonify({"error": "No file provided"}), 400

        file_data = uploaded_file.read()

        try:
            upload_request = FileUploadRequest(
                filename=uploaded_file.filename or "",
                data=file_data,
                mime_type=uploaded_file.content_type or "application/octet-stream",
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        try:
            file_record = self.file_service.upload_file(
                filename=upload_request.filename,
                data=upload_request.data,
                mime_type=upload_request.mime_type,
            )
        except (FileTooLargeError, FileTypeError) as e:
            return jsonify({"error": str(e)}), 400

        return jsonify({
            "url": f"/uploads/{file_record.file_id}/{file_record.original_filename}",
        }), 201

    def serve_file(self, file_id: str, filename: str):
        """Handle GET /uploads/<uuid>/<filename>.

        Retrieves a file record by UUID and streams the raw bytes.

        Args:
            file_id: UUID of the uploaded file.
            filename: Original filename (URL compatibility, not used for lookup).

        Returns:
            File stream with correct MIME type, or 404 JSON.
        """
        file_record = self.file_service.get_file(file_id)
        if file_record is None:
            return jsonify({"error": "File not found"}), 404

        return send_file(
            BytesIO(file_record.data),
            mimetype=file_record.mime_type,
            as_attachment=False,
            download_name=file_record.original_filename,
        )
