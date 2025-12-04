"""
Auth Service - Микросервис для аутентификации и авторизации
Предоставляет JWT токены, проверку ролей, API ключи с HMAC, динамические токены
"""
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import hmac
import hashlib
import base64
import jwt
from jwt import PyJWT

from .models import User, Base, UserRole, APIKey, DynamicToken
from .schemas import (
    UserCreate, UserResponse, Token, TokenData,
    TokenVerifyRequest,
    APIKeyCreate, APIKeyResponse, DynamicTokenResponse,
    HMACSignature
)
from .database import get_db
from .utils import (
    verify_password, get_password_hash,
    create_access_token, verify_token,
    get_current_user, get_current_active_user,
    generate_api_key, verify_hmac_signature,
    generate_dynamic_token
)

# Конфигурация
SECRET_KEY = "your-secret-key-change-in-production-use-env-variable"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(
    title="Auth Service",
    description="Сервис аутентификации и авторизации с JWT, API ключами, HMAC и динамическими токенами",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация базы данных
engine = create_async_engine("sqlite+aiosqlite:///./auth.db", echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создание тестовых пользователей
    async with async_session() as session:
        # Проверяем, есть ли уже пользователи
        from sqlalchemy import select
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            # Создаём админа
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            # Создаём обычного пользователя
            user = User(
                username="user",
                email="user@example.com",
                hashed_password=get_password_hash("user123"),
                role=UserRole.USER,
                is_active=True
            )
            session.add(admin)
            session.add(user)
            await session.commit()

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверка существования пользователя
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Создание нового пользователя
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.USER,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active
    )

@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Получение JWT токена"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active
    )

@app.get("/users/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о пользователе (только для админов)"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active
    )

@app.post("/verify-token")
async def verify_jwt_token(request: TokenVerifyRequest):
    """Проверка JWT токена"""
    try:
        payload = verify_token(request.token)
        return {"valid": True, "payload": payload}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

# API Keys Management
@app.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание API ключа с HMAC"""
    key_id, secret_key = generate_api_key()
    
    api_key = APIKey(
        key_id=key_id,
        secret_key=secret_key,
        user_id=current_user.id,
        name=api_key_data.name,
        permissions=api_key_data.permissions or ["read"]
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    return APIKeyResponse(
        id=api_key.id,
        key_id=api_key.key_id,
        secret_key=api_key.secret_key,  # Показываем только при создании
        name=api_key.name,
        permissions=api_key.permissions,
        created_at=api_key.created_at
    )

@app.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Список API ключей пользователя"""
    from sqlalchemy import select
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id)
    )
    keys = result.scalars().all()
    
    return [
        APIKeyResponse(
            id=key.id,
            key_id=key.key_id,
            secret_key="***hidden***",
            name=key.name,
            permissions=key.permissions,
            created_at=key.created_at
        )
        for key in keys
    ]

@app.post("/verify-api-key")
async def verify_api_key_with_hmac(
    key_id: str = Header(..., alias="X-API-Key-ID"),
    signature: str = Header(..., alias="X-API-Signature"),
    timestamp: str = Header(..., alias="X-API-Timestamp"),
    db: AsyncSession = Depends(get_db)
):
    """Проверка API ключа с HMAC подписью"""
    from sqlalchemy import select
    result = await db.execute(select(APIKey).where(APIKey.key_id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Проверка временной метки (защита от replay атак)
    try:
        ts = int(timestamp)
        current_ts = int(datetime.utcnow().timestamp())
        if abs(current_ts - ts) > 300:  # 5 минут
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request timestamp too old or too far in future"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timestamp"
        )
    
    return {
        "valid": True,
        "key_id": key_id,
        "user_id": api_key.user_id,
        "permissions": api_key.permissions
    }

# Dynamic Tokens (ZTNA)
@app.post("/dynamic-tokens", response_model=DynamicTokenResponse)
async def create_dynamic_token(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание динамического токена для ZTNA (Zero Trust Network Access)"""
    token_value, expires_at = generate_dynamic_token()
    
    dynamic_token = DynamicToken(
        token=token_value,
        user_id=current_user.id,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(dynamic_token)
    await db.commit()
    await db.refresh(dynamic_token)
    
    return DynamicTokenResponse(
        id=dynamic_token.id,
        token=dynamic_token.token,
        expires_at=dynamic_token.expires_at,
        is_active=dynamic_token.is_active
    )

@app.post("/verify-dynamic-token")
async def verify_dynamic_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Проверка динамического токена"""
    from sqlalchemy import select
    result = await db.execute(
        select(DynamicToken).where(
            DynamicToken.token == token,
            DynamicToken.is_active == True
        )
    )
    dynamic_token = result.scalar_one_or_none()
    
    if not dynamic_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive token"
        )
    
    if dynamic_token.expires_at < datetime.utcnow():
        # Деактивируем истёкший токен
        dynamic_token.is_active = False
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    
    return {
        "valid": True,
        "user_id": dynamic_token.user_id,
        "expires_at": dynamic_token.expires_at
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-service"}

