"""Error handling utilities."""
import logging
from fastapi.responses import JSONResponse

# Setup logging
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)


class InvalidParameterError(APIError):
    """Exception for invalid parameter errors."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class DatabaseError(APIError):
    """Exception for database errors."""

    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=detail)


class QueryBuildError(APIError):
    """Exception for query building errors."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


def handle_exceptions(exc: Exception) -> JSONResponse:
    """Handle exceptions and return appropriate responses."""
    if isinstance(exc, APIError):
        status_code = exc.status_code
        detail = exc.detail
    else:
        # Generic error handling
        logger.error(f"Unhandled exception: {str(exc)}")
        status_code = 500
        detail = f"Internal server error: {str(exc)}"

    return JSONResponse(
        status_code=status_code,
        content={"error": detail}
    )