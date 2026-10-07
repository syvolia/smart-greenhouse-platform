"""Convert uncaught exceptions into a consistent JSON envelope."""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": "Internal server error",
                "path": request.url.path,
            }
        },
    )