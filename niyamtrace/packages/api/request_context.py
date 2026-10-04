import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Generate Request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Idempotency Key logic for POST/PUT requests
        if request.method in ["POST", "PUT"]:
            idempotency_key = request.headers.get("x-idempotency-key")
            # In a real app we'd validate this against a cache/store.
            request.state.idempotency_key = idempotency_key

        try:
            response = await call_next(request)
        except Exception:
            raise

        response.headers["X-Request-ID"] = request_id
        
        # If trace_id was attached to request state (e.g. by pipeline), attach to header
        if hasattr(request.state, "trace_id"):
            response.headers["X-Trace-ID"] = request.state.trace_id

        return response
