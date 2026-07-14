import importlib
import sys

from fastapi import FastAPI

from src.shared.infrastructure import factory, logging_configuration


class TestApplicationBootstrap:
    def test_configures_logging_and_exposes_asgi_app(self, monkeypatch):
        logging_calls = []
        expected_app = FastAPI()

        def configure_logging_spy():
            logging_calls.append("configured")

        def create_app_stub():
            return expected_app

        monkeypatch.setattr(
            logging_configuration, "configure_logging", configure_logging_spy
        )
        monkeypatch.setattr(factory, "create_app", create_app_stub)
        sys.modules.pop("src.main", None)

        try:
            main = importlib.import_module("src.main")

            assert logging_calls == ["configured"]
            assert main.app is expected_app
        finally:
            sys.modules.pop("src.main", None)
