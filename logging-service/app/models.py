"""Модели данных для Logging Service"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    service = Column(String, index=True, nullable=False)  # Название сервиса
    endpoint = Column(String, nullable=False)  # Путь эндпоинта
    method = Column(String, nullable=False)  # HTTP метод
    user_id = Column(String, nullable=True)  # ID пользователя
    user_role = Column(String, nullable=True)  # Роль пользователя
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    request_body = Column(Text, nullable=True)  # JSON строка
    response_status = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=True)  # JSON строка
    execution_time_ms = Column(Float, nullable=True)  # Время выполнения в мс
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

