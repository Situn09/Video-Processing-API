# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Alias (so you can import `async_session`)
async_session = AsyncSessionLocal

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
