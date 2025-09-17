from fastapi import FastAPI
from app.api.v1 import router as v1
from app.db import base
from app.db.session import engine
import asyncio
from app.core.config import settings

app = FastAPI(title="Video Processing API")
app.include_router(v1, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # create tables - in prod use migrations
    async with engine.begin() as conn:
        await conn.run_sync(base.Base.metadata.create_all)
