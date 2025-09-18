import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Video Processing API"
    DEBUG: bool = True
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/video_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "/app/static/processed_videos")
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    class Config:
        env_file = ".env"

settings = Settings()
