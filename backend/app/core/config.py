import os
from venv import logger
from pydantic_settings import BaseSettings
import dotenv
dotenv.load_dotenv()
from pathlib import Path
from app.log import logger

# Default relative storage path
default_storage = Path("static/processed_videos")

# Use env variable if provided, else default
storage_path = Path(os.getenv("STORAGE_PATH", default_storage)).resolve()
logger.info(f"Using storage path: {storage_path}")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Video Processing API"
    DEBUG: bool = True
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/video_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    STORAGE_PATH: str = str(storage_path)
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    class Config:
        env_file = ".env"

settings = Settings()
logger.info(f"Using storage path using settings: {settings.STORAGE_PATH}")
