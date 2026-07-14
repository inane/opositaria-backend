from src.shared.infrastructure.factory import create_app
from src.shared.infrastructure.logging_configuration import configure_logging


configure_logging()
app = create_app()
