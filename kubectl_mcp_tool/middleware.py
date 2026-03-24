"""Pure ASGI middleware for bearer token extraction.

Extracts the Authorization header from incoming HTTP requests and stores
the bearer token in a contextvar so downstream tool handlers and K8s
client code can use it for per-request authentication.

NOTE: This is a pure ASGI middleware (NOT BaseHTTPMiddleware) to avoid
incompatibility with SSE streaming responses. BaseHTTPMiddleware wraps
the response body iterator which breaks SSE's long-lived streaming.
"""

import logging
from starlette.types import ASGIApp, Receive, Scope, Send

from .bearer_token import set_bearer_token, reset_bearer_token

logger = logging.getLogger("mcp-server")


class BearerTokenMiddleware:
    """Extract Authorization Bearer token from requests and store in contextvar.

    This middleware intercepts all incoming HTTP requests, extracts the
    Bearer token from the Authorization header (if present), and makes it
    available via the bearer_token contextvar for the duration of the request.

    Implemented as a pure ASGI middleware to be compatible with SSE streaming.
    The token is automatically cleaned up after the request completes.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract bearer token from headers
        token = None
        headers = dict(scope.get("headers", []))
        auth_header_value = headers.get(b"authorization", b"").decode("latin-1")

        if auth_header_value.lower().startswith("bearer "):
            token = auth_header_value[7:]  # Strip "Bearer " prefix
            logger.info("Bearer token extracted from Authorization header (length=%d)", len(token))

        ctx_token = set_bearer_token(token)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_bearer_token(ctx_token)
