import logging
import sys

from app.middleware.request_id import RequestIdFilter


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide structured logging with request IDs."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | req=%(request_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)