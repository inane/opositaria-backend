import json
import logging
import sys
from collections.abc import Sequence


_safe_context_fields = (
    "event",
    "operation",
    "documentType",
    "documentFormat",
    "status",
    "errorType",
)


class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _safe_context_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                log_entry[field] = self._safe_value(value)
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

    @staticmethod
    def _safe_value(value):
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            return str(value)


def _create_default_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    setattr(handler, "_zebra_application_logging_handler", True)
    return handler


def _has_default_handler(root_logger: logging.Logger) -> bool:
    return any(
        getattr(handler, "_zebra_application_logging_handler", False)
        for handler in root_logger.handlers
    )


def configure_logging(
    level: int = logging.INFO,
    handlers: Sequence[logging.Handler] | None = None,
) -> None:
    formatter = StructuredLogFormatter()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if handlers is None:
        handlers = (
            [] if _has_default_handler(root_logger) else [_create_default_handler()]
        )

    for handler in handlers:
        handler.setFormatter(formatter)
        if handler not in root_logger.handlers:
            root_logger.addHandler(handler)
