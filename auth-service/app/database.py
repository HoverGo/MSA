"""Настройка базы данных"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# SQLite для простоты демонстрации
DATABASE_URL = "sqlite+aiosqlite:///./auth.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """Dependency для получения сессии БД"""
    async with async_session() as session:
        yield session

