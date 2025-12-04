"""Pydantic схемы для валидации данных"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DataItemCreate(BaseModel):
    title: str
    content: str

class DataItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class DataItemResponse(BaseModel):
    id: int
    title: str
    content: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

