"""
Middleware for the Interoperability Messaging Lab API.
Provides request ID tracking and timing capabilities.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add to request state
        request.state.request_id = request_id

        # Add to response headers
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request timing."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Record start time
        start_time = time.time()

        # Process request
        response: Response = await call_next(request)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Ensure minimum timing value (at least 1ms) to avoid zero
        processing_time_ms = max(int(processing_time * 1000), 1)

        # Add timing headers
        response.headers["X-Processing-Time"] = str(processing_time)
        response.headers["X-Processing-Time-MS"] = str(processing_time_ms)

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get request ID from state
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request start
        print(f"[{request_id}] {request.method} {request.url.path} - Started")

        try:
            # Process request
            response: Response = await call_next(request)

            # Log successful response
            print(f"[{request_id}] {request.method} {request.url.path} - {response.status_code} - Completed")

            return response

        except Exception as e:
            # Log error
            print(f"[{request_id}] {request.method} {request.url.path} - Error: {e}")
            raise
