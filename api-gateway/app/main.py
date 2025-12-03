"""
API Gateway - Центральная точка входа для всех микросервисов
Реализует: маршрутизацию, rate limiting, WAF, ZTNA, проверку JWT, логирование
"""
from fastapi import FastAPI, Request, Response, HTTPException, status, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict
import httpx
import os
import time
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .middleware.waf import WAFMiddleware
from .middleware.ztna import ZTNAMiddleware
from .middleware.logging import LoggingMiddleware
from .utils.rate_limiter import RateLimiter
from .utils.service_mesh import ServiceMesh
from .config import settings

app = FastAPI(
    title="API Gateway",
    description="Центральный шлюз с маршрутизацией, rate limiting, WAF, ZTNA",
    version="1.0.0"
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Инициализация компонентов
rate_limiter = RateLimiter()
service_mesh = ServiceMesh()
logging_middleware = LoggingMiddleware()

# Добавление middleware
app.add_middleware(WAFMiddleware)
app.add_middleware(ZTNAMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Маршрутизация сервисов
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
    "data": os.getenv("DATA_SERVICE_URL", "http://data-service:8002"),
    "logging": os.getenv("LOGGING_SERVICE_URL", "http://logging-service:8003"),
}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "services": {name: await service_mesh.check_health(url) for name, url in SERVICES.items()}
    }

@app.get("/")
async def root():
    """Информация о API Gateway"""
    return {
        "message": "API Gateway",
        "version": "1.0.0",
        "available_services": list(SERVICES.keys()),
        "documentation": "/docs"
    }

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@limiter.limit("5/second")
async def proxy_request(
    request: Request,
    service: str,
    path: str
):
    """
    Проксирование запросов к микросервисам
    Включает проверку JWT, rate limiting, WAF, ZTNA
    """
    start_time = time.time()
    
    # Проверка существования сервиса
    if service not in SERVICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service}' not found"
        )
    
    service_url = SERVICES[service]
    
    # Проверка доступности сервиса через Service Mesh
    if not await service_mesh.is_service_available(service):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service '{service}' is currently unavailable"
        )
    
    # Получение заголовков и тела запроса
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Проверка JWT для защищённых сервисов (кроме auth-service)
    if service != "auth":
        auth_header = headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Проверка токена через Auth Service
        token = auth_header.replace("Bearer ", "")
        try:
            async with httpx.AsyncClient() as client:
                verify_response = await client.post(
                    f"{SERVICES['auth']}/verify-token",
                    json={"token": token},
                    timeout=5.0
                )
                if verify_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token"
                    )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )
    
    # Получение тела запроса
    body = await request.body()
    
    # Проксирование запроса
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            target_url = f"{service_url}/{path}"
            
            # Добавляем query параметры
            if request.url.query:
                target_url += f"?{request.url.query}"
            
            proxy_response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None
            )
            
            # Логирование запроса
            execution_time = (time.time() - start_time) * 1000  # в миллисекундах
            
            # Парсинг request body
            request_body = None
            if body:
                try:
                    request_body = json.loads(body.decode("utf-8"))
                except:
                    request_body = None
            
            # Парсинг response body
            response_body = None
            content_type = proxy_response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    response_body = proxy_response.json()
                except:
                    response_body = None
            
            await logging_middleware.log_request(
                service=service,
                endpoint=path,
                method=request.method,
                ip_address=get_remote_address(request),
                user_agent=headers.get("user-agent"),
                request_body=request_body,
                response_status=proxy_response.status_code,
                response_body=response_body,
                execution_time_ms=execution_time
            )
            
            # Возврат ответа
            if "application/json" in content_type:
                try:
                    return JSONResponse(
                        content=proxy_response.json(),
                        status_code=proxy_response.status_code,
                        headers=dict(proxy_response.headers)
                    )
                except:
                    pass
            
            return Response(
                content=proxy_response.content,
                status_code=proxy_response.status_code,
                headers=dict(proxy_response.headers),
                media_type=content_type
            )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Service request timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway error: {str(e)}"
        )

@app.get("/services")
async def list_services():
    """Список доступных сервисов и их статус"""
    service_status = {}
    for name, url in SERVICES.items():
        service_status[name] = {
            "url": url,
            "available": await service_mesh.is_service_available(name),
            "health": await service_mesh.check_health(url)
        }
    return service_status

