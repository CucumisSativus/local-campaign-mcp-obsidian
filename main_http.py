#!/usr/bin/env python3
"""MCP Server for RPG Campaign Management with HTTP/SSE transport and authentication.

This server provides tools to access RPG campaign location data stored in markdown files.
It uses HTTP with Server-Sent Events (SSE) transport and requires API key authentication.
"""

import os
import sys
from pathlib import Path

import uvicorn
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

# Import the MCP server app and initialization functions from main.py
from main import (
    app,
    get_characters_directory,
    get_locations_directory,
    get_sessions_directory,
)

# Global variables for directories
_locations_dir: Path | None = None
_characters_dir: Path | None = None
_sessions_dir: Path | None = None


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate requests using API key."""

    def __init__(self, app, api_key: str) -> None:  # type: ignore[no-untyped-def]
        """Initialize the middleware with the required API key.

        Args:
            app: The ASGI application
            api_key: The valid API key for authentication
        """
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def, misc]
        """Check API key in request headers.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response object
        """
        # Allow health check endpoint without authentication
        if request.url.path == "/health":
            return await call_next(request)  # type: ignore[no-any-return]

        # Check for API key in Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return Response(
                content="Missing Authorization header",
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="API Key Required"'},
            )

        # Support both "Bearer <key>" and just "<key>" formats
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:]
        else:
            provided_key = auth_header

        if provided_key != self.api_key:
            return Response(
                content="Invalid API key",
                status_code=403,
            )

        response = await call_next(request)
        return response  # type: ignore[no-any-return]


async def health_check(request: Request) -> Response:
    """Health check endpoint.

    Args:
        request: The incoming request

    Returns:
        Response indicating server health
    """
    return Response(content="OK", status_code=200)


async def handle_sse(request: Request) -> Response:  # type: ignore[misc]
    """Handle SSE connection for MCP.

    Args:
        request: The incoming request

    Returns:
        SSE response with MCP communication
    """
    global _locations_dir, _characters_dir, _sessions_dir

    # Initialize directories if not already done
    if _locations_dir is None:
        _locations_dir = get_locations_directory()
    if _characters_dir is None:
        _characters_dir = get_characters_directory()
    if _sessions_dir is None:
        _sessions_dir = get_sessions_directory()

    # Import the global directory variables in main.py
    import main

    main._locations_dir = _locations_dir
    main._characters_dir = _characters_dir
    main._sessions_dir = _sessions_dir

    # Create SSE transport
    sse = SseServerTransport("/messages")

    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,  # type: ignore[attr-defined]
    ) as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options(),
        )

    return Response()


def get_api_key() -> str:
    """Get API key from environment variable.

    Returns:
        API key string

    Raises:
        SystemExit: If API_KEY is not set
    """
    api_key = os.environ.get("API_KEY")

    if not api_key:
        print(
            "Error: API_KEY environment variable is not set.\n"
            "Please set it to a secure random string for authentication.\n"
            "Example: export API_KEY=$(python -c 'import secrets; "
            "print(secrets.token_urlsafe(32))')",
            file=sys.stderr,
        )
        sys.exit(1)

    return api_key


def create_app() -> Starlette:
    """Create and configure the Starlette application.

    Returns:
        Configured Starlette application
    """
    api_key = get_api_key()

    # Create the application with authentication middleware
    application = Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
            Route("/sse", handle_sse, methods=["GET"]),
            Route("/messages", handle_sse, methods=["POST"]),
        ],
        middleware=[
            Middleware(APIKeyAuthMiddleware, api_key=api_key),
        ],
    )

    return application


def main() -> None:
    """Run the HTTP server with authentication."""
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    # Create the application
    application = create_app()

    print(f"Starting MCP server on {host}:{port}")
    print("Authentication: API Key required in Authorization header")
    print("Endpoints:")
    print(f"  - Health check: http://{host}:{port}/health")
    print(f"  - SSE endpoint: http://{host}:{port}/sse")

    # Run the server
    uvicorn.run(
        application,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
