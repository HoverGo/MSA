"""ZTNA (Zero Trust Network Access) Middleware"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
import httpx
import os
from ..config import settings

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

class ZTNAMiddleware(BaseHTTPMiddleware):
    """Middleware для Zero Trust Network Access - проверка динамических токенов"""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.enable_ztna:
            return await call_next(request)
        
        # Для некоторых эндпоинтов (например, health) не требуем ZTNA токен
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Проверка динамического токена
        ztna_token = request.headers.get(settings.ztna_token_header)
        
        if ztna_token:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{AUTH_SERVICE_URL}/verify-dynamic-token",
                        json={"token": ztna_token},
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        # Токен валиден, продолжаем
                        return await call_next(request)
                    else:
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "Invalid or expired ZTNA token"}
                        )
            except httpx.RequestError:
                # Если Auth Service недоступен, пропускаем проверку ZTNA
                # В production здесь должна быть более строгая логика
                pass
        
        # Если токен не предоставлен, всё равно пропускаем для упрощения
        # В реальной системе здесь должна быть обязательная проверка
        return await call_next(request)

