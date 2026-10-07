import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide structured logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Uvicorn access logs are noisy; keep warnings and above.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
