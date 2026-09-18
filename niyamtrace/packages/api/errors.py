import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from packages.config import get_settings

logger = logging.getLogger(__name__)

class NiyamAPIError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: dict = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

async def api_error_handler(request: Request, exc: NiyamAPIError):
    settings = get_settings()
    
    # Do not leak internal details in production unless debug is explicitly enabled
    # Actually, NiyamAPIError is our structured error, so we can return its message.
    response_content = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    }
    
    # We could inject trace_id if available in request.state
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        response_content["error"]["trace_id"] = trace_id
        
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception in API")
    settings = get_settings()
    message = "Internal Server Error"
    if settings.debug_mode:
        message = str(exc)
        
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": message}}
    )
