"""Конфигурация API Gateway"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Сервисы
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    data_service_url: str = os.getenv("DATA_SERVICE_URL", "http://data-service:8002")
    logging_service_url: str = os.getenv("LOGGING_SERVICE_URL", "http://logging-service:8003")
    
    # Rate Limiting
    rate_limit_per_second: int = 5
    rate_limit_per_minute: int = 100
    
    # WAF настройки
    enable_waf: bool = True
    blocked_patterns: list = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"SELECT.*FROM",
        r"DROP.*TABLE",
        r"UNION.*SELECT"
    ]
    
    # ZTNA настройки
    enable_ztna: bool = True
    ztna_token_header: str = "X-ZTNA-Token"
    
    class Config:
        env_file = ".env"

settings = Settings()

