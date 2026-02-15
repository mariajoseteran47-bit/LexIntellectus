from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import logging

logger = logging.getLogger("api.request")

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        user_id = "anonymous"
        if hasattr(request.state, "user"):
             user_id = str(request.state.user.id)
        
        # Log only significant actions or errors
        if request.method != "GET" or response.status_code >= 400:
            logger.info(
                f"Method={request.method} Path={request.url.path} "
                f"Status={response.status_code} User={user_id} "
                f"Time={process_time:.4f}s"
            )
            
        return response
