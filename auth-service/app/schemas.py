"""Pydantic схемы для валидации данных"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import UserRole

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class TokenVerifyRequest(BaseModel):
    token: str

class DynamicTokenVerifyRequest(BaseModel):
    token: str

class APIKeyCreate(BaseModel):
    name: str
    permissions: Optional[List[str]] = None

class APIKeyResponse(BaseModel):
    id: int
    key_id: str
    secret_key: str
    name: str
    permissions: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DynamicTokenResponse(BaseModel):
    id: int
    token: str
    expires_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class HMACSignature(BaseModel):
    key_id: str
    signature: str
    timestamp: str

