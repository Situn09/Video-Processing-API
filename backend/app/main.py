# backend/app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.router import router as v1_router
from app.db import base
from app.db.session import engine
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    async with engine.begin() as conn:
        await conn.run_sync(base.Base.metadata.create_all)

    yield  # 👈 this marks the point where the app starts serving

    # Shutdown logic (if needed, e.g., closing connections, cleaning up)
    print("👋 App shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)
    app.include_router(v1_router, prefix="/api/v1")
    return app

app = create_app()