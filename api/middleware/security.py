"""Security middleware for adding security headers and request validation."""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "1048576"))  # 1MB default
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses.

    Implements OWASP recommended security headers:
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - Content-Security-Policy: XSS protection
    - X-XSS-Protection: Legacy XSS protection
    - Referrer-Policy: Controls referrer information
    - Strict-Transport-Security: HTTPS enforcement (production only)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Add security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Referrer-Policy"
        ] = "strict-origin-when-cross-origin"

        # HSTS only in production (requires HTTPS)
        if ENVIRONMENT == "production":
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent memory exhaustion attacks.

    Checks Content-Length header and rejects requests exceeding limit.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and check size limit.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response or 413 error if request too large
        """
        # Check Content-Length header
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)

            if content_length > MAX_REQUEST_SIZE:
                logger.warning(
                    f"Request rejected: size {content_length} bytes "
                    f"exceeds limit {MAX_REQUEST_SIZE} bytes"
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. "
                        f"Maximum size: {MAX_REQUEST_SIZE} bytes"
                    },
                )

        return await call_next(request)
