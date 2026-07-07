import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception with structured error data."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "bad_request",
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, entity: str = "Resource", entity_id: int | str | None = None):
        msg = f"{entity} not found"
        if entity_id:
            msg += f": {entity_id}"
        super().__init__(msg, status_code=status.HTTP_404_NOT_FOUND, error_code="not_found")


class ForbiddenException(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, error_code="forbidden")


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, error_code="unauthorized")


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, error_code="conflict")


class ValidationException(AppException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, error_code="validation_error", details=details)


def error_response(status_code: int, message: str, error_code: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {},
            }
        },
    )


async def app_exception_handler(request: Request, exc: AppException):
    logger.warning("AppException: %s [%s]", exc.message, exc.error_code)
    return error_response(exc.status_code, exc.message, exc.error_code, exc.details)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = {
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "too_many_requests",
        500: "internal_error",
    }.get(exc.status_code, "http_error")
    return error_response(exc.status_code, exc.detail, code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = {}
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        details[loc] = err.get("msg", "Invalid value")
    return error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Request validation failed",
        "validation_error",
        details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "An unexpected error occurred",
        "internal_error",
    )
