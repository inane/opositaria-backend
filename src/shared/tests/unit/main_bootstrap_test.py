import pytest


class TestApplicationBootstrap:
    def test_configures_logging_on_import(self):
        """Skip: no main.py entrypoint exists yet."""
        pytest.skip("No main.py entrypoint exists yet")
