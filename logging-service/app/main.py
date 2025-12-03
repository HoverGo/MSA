"""
Logging Service - Микросервис для логирования и аудита активности
Хранит логи запросов, аудит действий пользователей
"""
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional
import json

from .models import AuditLog, Base
from .schemas import AuditLogCreate, AuditLogResponse, LogQuery
from .database import get_db, init_db

app = FastAPI(
    title="Logging Service",
    description="Сервис для логирования и аудита активности",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "logging-service"}

@app.post("/logs", status_code=status.HTTP_201_CREATED)
async def create_log(
    log_data: AuditLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание новой записи аудита"""
    log = AuditLog(
        service=log_data.service,
        endpoint=log_data.endpoint,
        method=log_data.method,
        user_id=log_data.user_id,
        user_role=log_data.user_role,
        ip_address=log_data.ip_address,
        user_agent=log_data.user_agent,
        request_body=json.dumps(log_data.request_body) if log_data.request_body else None,
        response_status=log_data.response_status,
        response_body=json.dumps(log_data.response_body) if log_data.response_body else None,
        execution_time_ms=log_data.execution_time_ms
    )
    
    db.add(log)
    await db.commit()
    await db.refresh(log)
    
    return {"id": log.id, "status": "logged"}

@app.get("/logs", response_model=List[AuditLogResponse])
async def get_logs(
    query: LogQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Получение логов с фильтрацией"""
    from sqlalchemy import select, and_
    from datetime import datetime, timedelta
    
    conditions = []
    
    if query.service:
        conditions.append(AuditLog.service == query.service)
    if query.user_id:
        conditions.append(AuditLog.user_id == query.user_id)
    if query.method:
        conditions.append(AuditLog.method == query.method)
    if query.status_code:
        conditions.append(AuditLog.response_status == query.status_code)
    if query.start_time:
        conditions.append(AuditLog.timestamp >= query.start_time)
    if query.end_time:
        conditions.append(AuditLog.timestamp <= query.end_time)
    
    query_obj = select(AuditLog)
    if conditions:
        query_obj = query_obj.where(and_(*conditions))
    
    query_obj = query_obj.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query_obj)
    logs = result.scalars().all()
    
    return [
        AuditLogResponse(
            id=log.id,
            service=log.service,
            endpoint=log.endpoint,
            method=log.method,
            user_id=log.user_id,
            user_role=log.user_role,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            request_body=json.loads(log.request_body) if log.request_body else None,
            response_status=log.response_status,
            response_body=json.loads(log.response_body) if log.response_body else None,
            execution_time_ms=log.execution_time_ms,
            timestamp=log.timestamp
        )
        for log in logs
    ]

@app.get("/logs/stats")
async def get_logs_stats(
    service: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики по логам"""
    from sqlalchemy import select, func, and_
    
    conditions = []
    if service:
        conditions.append(AuditLog.service == service)
    
    query_obj = select(
        func.count(AuditLog.id).label("total"),
        func.avg(AuditLog.response_status).label("avg_status"),
        func.avg(AuditLog.execution_time_ms).label("avg_time"),
        func.count(func.distinct(AuditLog.user_id)).label("unique_users")
    )
    
    if conditions:
        query_obj = query_obj.where(and_(*conditions))
    
    result = await db.execute(query_obj)
    stats = result.first()
    
    return {
        "total_requests": stats.total or 0,
        "average_status": stats.avg_status or 0,
        "average_execution_time_ms": stats.avg_time or 0,
        "unique_users": stats.unique_users or 0
    }

