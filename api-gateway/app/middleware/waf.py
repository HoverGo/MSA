"""WAF (Web Application Firewall) Middleware"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
import re
from ..config import settings

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
        
        # Проверка заголовков
        headers_str = str(dict(request.headers))
        for pattern in settings.blocked_patterns:
            if re.search(pattern, headers_str, re.IGNORECASE):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Request blocked by WAF: suspicious headers"}
                )
        
        return await call_next(request)

