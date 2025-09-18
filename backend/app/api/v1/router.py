from fastapi import APIRouter
from . import video, editing, jobs

router = APIRouter()
router.include_router(video.router)
router.include_router(editing.router)
router.include_router(jobs.router)

# ✅ Test endpoint
@router.get("/ping")
async def ping():
    return {"message": "api is up!"}
