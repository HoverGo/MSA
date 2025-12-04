"""WAF (Web Application Firewall) Middleware"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Message
from fastapi import status
import re
from ..config import settings


async def _clone_request_with_body(request: Request, body: bytes) -> Request:
    """Re-create request with preserved body so downstream middleware can consume it."""

    async def receive() -> Message:
        return {"type": "http.request", "body": body, "more_body": False}

    cloned = Request(request.scope, receive=receive)
    cloned._body = body
    return cloned

class WAFMiddleware(BaseHTTPMiddleware):
    """Middleware для защиты от различных атак"""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.enable_waf:
            return await call_next(request)
        
        # Проверка URL
        url = str(request.url)
        for pattern in settings.blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Request blocked by WAF: suspicious pattern detected"}
                )
        
        cloned_request = request

        # Проверка тела запроса
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode("utf-8", errors="ignore")

            for pattern in settings.blocked_patterns:
                if re.search(pattern, body_str, re.IGNORECASE):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Request blocked by WAF: suspicious content detected"}
                    )

            cloned_request = await _clone_request_with_body(request, body)
        
        # Проверка заголовков
        headers_str = str(dict(request.headers))
        for pattern in settings.blocked_patterns:
            if re.search(pattern, headers_str, re.IGNORECASE):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Request blocked by WAF: suspicious headers"}
                )
        
        return await call_next(cloned_request)

