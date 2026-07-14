import logging
import sys
from io import StringIO

import pytest

from src.shared.infrastructure.logging_configuration import configure_logging


class TestConfigureLogging:
    @pytest.fixture(autouse=True)
    def restore_root_logger(self):
        root_logger = logging.getLogger()
        original_handlers = list(root_logger.handlers)
        original_level = root_logger.level
        root_logger.handlers = []

        yield

        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)

    def test_installs_structured_json_formatter(self):
        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        formatter = handler.formatter
        assert formatter is not None

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)

        import json

        parsed = json.loads(formatted)
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"

    def test_does_not_create_duplicate_handlers_on_repeated_calls(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])
        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.idempotent")
        logger.info("Single message")

        output = stream.getvalue()
        assert output.count("Single message") == 1

    def test_does_not_create_duplicate_default_handlers_on_repeated_calls(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        stream = StringIO()
        monkeypatch.setattr(sys, "stdout", stream)

        configure_logging()
        configure_logging()

        logger = logging.getLogger("test.default.idempotent")
        logger.info("Single default message")

        output = stream.getvalue()
        assert output.count("Single default message") == 1

    def test_default_logging_level_is_info(self):
        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_emits_valid_json_per_log_line(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.json")
        logger.info("Hello structured world")

        output = stream.getvalue().strip()
        assert output

        import json

        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_records_required_structured_fields(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.required")
        logger.info("Required fields test")

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.required"
        assert parsed["message"] == "Required fields test"

    def test_preserves_message_interpolation(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.interpolation")
        logger.info("Hello %s", "world")

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert parsed["message"] == "Hello world"

    def test_records_event_context_field(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.event")
        logger.info(
            "Document extraction requested",
            extra={"event": "document_extraction_requested"},
        )

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert parsed["event"] == "document_extraction_requested"

    def test_records_operational_context_fields(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.operational")
        logger.info(
            "Operation completed",
            extra={
                "operation": "extract_document",
                "documentType": "invoice",
                "documentFormat": "pdf",
                "status": "success",
                "errorType": None,
            },
        )

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert parsed["operation"] == "extract_document"
        assert parsed["documentType"] == "invoice"
        assert parsed["documentFormat"] == "pdf"
        assert parsed["status"] == "success"
        assert parsed["errorType"] is None

    def test_handles_non_serializable_context_values(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.nonserializable")
        logger.info(
            "Non serializable context",
            extra={"event": {"nested", "set"}},
        )

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert "event" in parsed
        assert isinstance(parsed["event"], str)

    def test_omits_non_allowlisted_custom_attributes(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.disallowed")
        logger.info(
            "Disallowed context",
            extra={"password": "secret123", "customField": "value"},
        )

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert "password" not in parsed
        assert "customField" not in parsed
        assert "message" in parsed

    def test_preserves_warning_level(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.warning")
        logger.warning("Warning message")

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert parsed["level"] == "WARNING"

    def test_preserves_all_logging_levels(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(level=logging.DEBUG, handlers=[handler])

        logger = logging.getLogger("test.levels")

        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")

        output = stream.getvalue().strip()
        import json

        lines = output.splitlines()
        assert len(lines) == 4

        levels = [json.loads(line)["level"] for line in lines]
        assert levels == ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_records_exception_diagnostics(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        configure_logging(handlers=[handler])

        logger = logging.getLogger("test.exception")

        try:
            raise ValueError("Something went wrong")
        except ValueError:
            logger.exception("Unexpected failure")

        output = stream.getvalue().strip()
        import json

        parsed = json.loads(output)

        assert parsed["level"] == "ERROR"
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Something went wrong" in parsed["exception"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
