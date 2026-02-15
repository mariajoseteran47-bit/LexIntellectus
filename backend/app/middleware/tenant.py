"""
LexIntellectus - Tenant Middleware
Extracts tenant context from JWT claims and injects into request state.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.security import decode_token


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant_id from JWT token
    and makes it available in request.state for downstream use.
    """

    # Public paths that don't require tenant context
    PUBLIC_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }

    async def dispatch(self, request: Request, call_next):
        # Skip public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Try to extract tenant from Authorization header
        request.state.tenant_id = None
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload:
                request.state.tenant_id = payload.get("tenant_id")

        response = await call_next(request)
        return response
