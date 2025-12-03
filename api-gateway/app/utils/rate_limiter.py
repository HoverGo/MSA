"""Rate Limiter для ограничения количества запросов"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

class RateLimiter:
    """Простой in-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.rate_per_second = 5
        self.rate_per_minute = 100
    
    def is_allowed(self, identifier: str) -> bool:
        """Проверка, разрешён ли запрос"""
        now = datetime.utcnow()
        
        # Очистка старых запросов
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < timedelta(minutes=1)
        ]
        
        # Проверка лимита в секунду
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < timedelta(seconds=1)
        ]
        
        if len(recent_requests) >= self.rate_per_second:
            return False
        
        # Проверка лимита в минуту
        if len(self.requests[identifier]) >= self.rate_per_minute:
            return False
        
        # Добавляем текущий запрос
        self.requests[identifier].append(now)
        return True
    
    def reset(self, identifier: str):
        """Сброс счётчика для идентификатора"""
        self.requests.pop(identifier, None)

