# backend/app/main.py
from fastapi import FastAPI
from app.api.v1.router import router as v1_router
from app.db import base
from app.db.session import engine  # synchronous engine
from app.core.config import settings
from app.log import logger

# 1️⃣ Synchronous startup
logger.info("Creating tables if not exist...")
base.Base.metadata.create_all(bind=engine)
logger.info("Tables created successfully.")

# 2️⃣ Create FastAPI app normally
app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)
app.include_router(v1_router, prefix="/api/v1")  