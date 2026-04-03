"""Bearer token propagation via contextvars.

This module provides a request-scoped bearer token that can be injected
into Kubernetes API calls. The token is extracted from the incoming HTTP
Authorization header by the BearerTokenMiddleware and stored in a
contextvar so that tool handlers and K8s client creation code can access
it without any function signature changes.

Usage in tool handlers / k8s_config.py:
    from kubectl_mcp_tool.bearer_token import get_bearer_token
    token = get_bearer_token()  # Returns token string or None
"""

import contextvars
import logging
from typing import Optional

logger = logging.getLogger("mcp-server")

# Request-scoped bearer token. Set by BearerTokenMiddleware, read by k8s_config.
_bearer_token_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "bearer_token", default=None
)


def get_bearer_token() -> Optional[str]:
    """Get the bearer token for the current request context.

    First checks the contextvar set by BearerTokenMiddleware (works in SSE/custom
    HTTP modes where ASGI middleware and tool handlers share the same context).

    Falls back to extracting the Authorization header from the MCP request context
    (required for streamable-http mode where FastMCP runs tool handlers in a
    different async context than the ASGI middleware).

    Returns:
        The bearer token string (without 'Bearer ' prefix), or None if not set.
    """
    # Fast path: contextvar set by BearerTokenMiddleware (same async context)
    token = _bearer_token_var.get()
    if token:
        return token

    # Fallback: extract from MCP request context (streamable-http mode)
    try:
        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            logger.info(
                "Bearer token extracted from MCP request context (length=%d)",
                len(token),
            )
            return token
    except Exception:
        pass

    return None


def set_bearer_token(token: Optional[str]) -> contextvars.Token:
    """Set the bearer token for the current request context.

    Args:
        token: The bearer token string (without 'Bearer ' prefix).

    Returns:
        A contextvars.Token that can be used to reset the value.
    """
    return _bearer_token_var.set(token)


def reset_bearer_token(token: contextvars.Token) -> None:
    """Reset the bearer token to its previous value.

    Args:
        token: The contextvars.Token returned by set_bearer_token().
    """
    _bearer_token_var.reset(token)
