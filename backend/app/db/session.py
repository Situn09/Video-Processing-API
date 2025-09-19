# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create synchronous engine
engine = create_engine(
    settings.DATABASE_URL,  # should be sync URL, e.g., postgresql://user:pass@host/db
    future=True,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Dependency for FastAPI (sync version)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
