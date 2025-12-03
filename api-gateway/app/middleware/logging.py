"""Logging Middleware для аудита запросов"""
import httpx
import os
from typing import Optional, Dict, Any

LOGGING_SERVICE_URL = os.getenv("LOGGING_SERVICE_URL", "http://logging-service:8003")

class LoggingMiddleware:
    """Middleware для логирования всех запросов в Logging Service"""
    
    @staticmethod
    async def log_request(
        service: str,
        endpoint: str,
        method: str,
        ip_address: str,
        user_agent: Optional[str],
        request_body: Optional[Dict[str, Any]],
        response_status: int,
        response_body: Optional[Dict[str, Any]],
        execution_time_ms: float
    ):
        """Отправка лога в Logging Service"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{LOGGING_SERVICE_URL}/logs",
                    json={
                        "service": service,
                        "endpoint": endpoint,
                        "method": method,
                        "ip_address": ip_address,
                        "user_agent": user_agent,
                        "request_body": request_body,
                        "response_status": response_status,
                        "response_body": response_body,
                        "execution_time_ms": execution_time_ms
                    },
                    timeout=2.0  # Не блокируем основной запрос
                )
        except Exception:
            # В случае ошибки логирования не прерываем основной запрос
            pass

