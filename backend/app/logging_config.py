import logging

from app.config import get_settings

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper(), format=_LOG_FORMAT, force=True)

    # Trim noise from libraries that log per-request / per-statement at INFO.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
