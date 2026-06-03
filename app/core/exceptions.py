"""Domain exceptions and standard HTTP exception handlers."""

from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse


class ArchonException(Exception):
    """Base domain exception for Archon."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class EntityNotFoundException(ArchonException):
    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} with identifier '{identifier}' was not found.",
            status_code=404,
            code="NOT_FOUND",
        )


class UnauthorizedException(ArchonException):
    def __init__(self, message: str = "Invalid credentials or token expired."):
        super().__init__(message=message, status_code=401, code="UNAUTHORIZED")


class ForbiddenException(ArchonException):
    def __init__(self, message: str = "Access forbidden."):
        super().__init__(message=message, status_code=403, code="FORBIDDEN")


async def archon_exception_handler(request: Request, exc: ArchonException):
    """Global handler for domain ArchonException instances."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "code": exc.code,
            "details": exc.details,
        },
    )
