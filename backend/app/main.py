# # backend/app/main.py

# from fastapi import FastAPI
# from contextlib import asynccontextmanager
# from app.api.v1.router import router as v1_router
# from app.db import base
# from app.db.session import engine
# from app.core.config import settings
# from app.log import logger


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup logic
#     async with engine.begin() as conn:
#         await conn.run_sync(base.Base.metadata.create_all)
#     logger.info(" App starting up...")

#     yield  # 👈 this marks the point where the app starts serving

#     # Shutdown logic (if needed, e.g., closing connections, cleaning up)
#     print(" App shutting down...")

# def create_app() -> FastAPI:
#     app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)
#     app.include_router(v1_router, prefix="/api/v1")
#     return app

# app = create_app()

# # backend/app/main.py

# from fastapi import FastAPI
# from contextlib import contextmanager
# from app.api.v1.router import router as v1_router
# from app.db import base
# from app.db.session import engine
# from app.core.config import settings
# from app.log import logger


# @contextmanager
# def lifespan(app: FastAPI):
#     # Startup logic: create tables synchronously
#     base.Base.metadata.create_all(bind=engine)
#     logger.info("App starting up...")

#     yield  # 👈 app starts serving here

#     # Shutdown logic (if needed)
#     print("App shutting down...")


# def create_app() -> FastAPI:
#     app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)
#     app.include_router(v1_router, prefix="/api/v1")
#     return app


# app = create_app()


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