"""Unit tests for the UploadError DTO."""

import pytest

from src.study_documents.application.dtos import UploadError


class TestUploadError:
    """Tests for UploadError structured response."""

    def test_creates_with_code_and_safe_message(self) -> None:
        """An UploadError exposes only the error code and a safe message."""
        error = UploadError(
            code="file_too_large", message="File exceeds the 50 MB size limit"
        )

        assert error.code == "file_too_large"
        assert error.message == "File exceeds the 50 MB size limit"

    def test_creates_with_empty_upload_code(self) -> None:
        """An UploadError with empty_upload code preserves the code and message."""
        error = UploadError(code="empty_upload", message="Upload content is empty")

        assert error.code == "empty_upload"
        assert error.message == "Upload content is empty"

    def test_creates_with_invalid_file_type_code(self) -> None:
        """An UploadError with invalid_file_type code preserves the code and message."""
        error = UploadError(
            code="invalid_file_type", message="Only PDF files are accepted"
        )

        assert error.code == "invalid_file_type"
        assert error.message == "Only PDF files are accepted"

    def test_creates_with_invalid_filename_code(self) -> None:
        """An UploadError with invalid_filename code preserves the code and message."""
        error = UploadError(
            code="invalid_filename", message="Filename contains invalid characters"
        )

        assert error.code == "invalid_filename"
        assert error.message == "Filename contains invalid characters"

    def test_is_immutable(self) -> None:
        """An UploadError cannot be modified after creation."""
        error = UploadError(
            code="file_too_large", message="File exceeds the 50 MB size limit"
        )

        with pytest.raises(AttributeError):
            error.code = "empty_upload"  # type: ignore[misc]

    def test_exposes_only_code_and_message(self) -> None:
        """An UploadError has no fields beyond code and message."""
        error = UploadError(code="test_code", message="test message")

        fields = [f.name for f in type(error).__dataclass_fields__.values()]
        assert fields == ["code", "message"]
