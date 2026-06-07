from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
import structlog

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        
        # Bind request_id to structlog context
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        # Clear context
        structlog.contextvars.clear_contextvars()
        
        return response
