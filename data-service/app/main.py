"""
Data Service - Микросервис для хранения и управления данными
Проверяет права доступа через JWT токены от Auth Service
"""
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List
import httpx
import os

from .models import DataItem, Base
from .schemas import DataItemCreate, DataItemResponse, DataItemUpdate
from .database import get_db, init_db
from .utils import verify_jwt_token_from_auth_service

app = FastAPI(
    title="Data Service",
    description="Сервис для управления данными с проверкой прав доступа",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

@app.on_event("startup")
async def startup():
    await init_db()

async def get_current_user_from_token(
    authorization: Optional[str] = Header(None)
):
    """Проверка JWT токена через Auth Service"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    try:
        token = authorization.replace("Bearer ", "")
        token_data = await verify_jwt_token_from_auth_service(token)
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-service"}

@app.get("/data", response_model=List[DataItemResponse])
async def get_all_data(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Получение всех данных (только для авторизованных пользователей)"""
    from sqlalchemy import select
    result = await db.execute(
        select(DataItem)
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    
    return [DataItemResponse(
        id=item.id,
        title=item.title,
        content=item.content,
        owner_id=item.owner_id,
        created_at=item.created_at,
        updated_at=item.updated_at
    ) for item in items]

@app.get("/data/{item_id}", response_model=DataItemResponse)
async def get_data_item(
    item_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Получение конкретного элемента данных"""
    from sqlalchemy import select
    result = await db.execute(select(DataItem).where(DataItem.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Проверка прав доступа: пользователь может видеть только свои данные, админ - все
    # owner_id хранится как username (для упрощения)
    if current_user.get("role") != "admin" and str(item.owner_id) != current_user.get("username"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return DataItemResponse(
        id=item.id,
        title=item.title,
        content=item.content,
        owner_id=item.owner_id,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@app.post("/data", response_model=DataItemResponse, status_code=status.HTTP_201_CREATED)
async def create_data_item(
    item: DataItemCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового элемента данных"""
    new_item = DataItem(
        title=item.title,
        content=item.content,
        owner_id=current_user.get("username", "unknown")  # Используем username как owner_id
    )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    return DataItemResponse(
        id=new_item.id,
        title=new_item.title,
        content=new_item.content,
        owner_id=new_item.owner_id,
        created_at=new_item.created_at,
        updated_at=new_item.updated_at
    )

@app.put("/data/{item_id}", response_model=DataItemResponse)
async def update_data_item(
    item_id: int,
    item_update: DataItemUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Обновление элемента данных"""
    from sqlalchemy import select
    result = await db.execute(select(DataItem).where(DataItem.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Проверка прав доступа
    if current_user.get("role") != "admin" and str(item.owner_id) != current_user.get("username"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if item_update.title is not None:
        item.title = item_update.title
    if item_update.content is not None:
        item.content = item_update.content
    
    item.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(item)
    
    return DataItemResponse(
        id=item.id,
        title=item.title,
        content=item.content,
        owner_id=item.owner_id,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@app.delete("/data/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_item(
    item_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Удаление элемента данных (только для админов)"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete items"
        )
    
    from sqlalchemy import select
    result = await db.execute(select(DataItem).where(DataItem.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    await db.delete(item)
    await db.commit()
    
    return None

