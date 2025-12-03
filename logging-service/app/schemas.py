"""Pydantic схемы для валидации данных"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AuditLogCreate(BaseModel):
    service: str
    endpoint: str
    method: str
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_body: Optional[Dict[str, Any]] = None
    response_status: int
    response_body: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None

class AuditLogResponse(BaseModel):
    id: int
    service: str
    endpoint: str
    method: str
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_body: Optional[Dict[str, Any]] = None
    response_status: int
    response_body: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

class LogQuery(BaseModel):
    service: Optional[str] = None
    user_id: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

