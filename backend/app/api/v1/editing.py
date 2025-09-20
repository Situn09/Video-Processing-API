# app/api/v1/editing.py
import json
from typing import Optional
import uuid
from fastapi import APIRouter, Body, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.tasks.video import overlay_video_task, trim_video_task
from app.enums.job_status import JobStatus
from app.enums.task_type import TaskType
from app.repositories.job_repo import JobRepository
from app.log import logger
from app.schemas.overlay import OverlayConfigCreate
from app.repositories.video_repo import VideoRepository
from app.db.models.video import OverlayConfig
from app.services import storage

router = APIRouter(prefix="/edit", tags=["Editing"])


@router.post("/trim")
def trim_video(video_id: int, start: float, end: float, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    job_repo = JobRepository(db)
    logger.info(f"Creating trim job {job_id} for video {video_id} from {start} to {end}")

    # 1. Create job entry in DB (sync)
    job_repo.create(
        job_id=job_id,
        video_id=video_id,
        task=TaskType.TRIM.value,
        status=JobStatus.PENDING.value,
        meta={"start": start, "end": end}
    )
    db.commit()

    # 2. Enqueue Celery task
    trim_video_task.apply_async(args=[video_id, start, end, job_id], task_id=job_id)

    # 3. Return immediately
    return {"job_id": job_id, "video_id": video_id}

def req_model(req: str = Form(...)) -> OverlayConfigCreate:
    return OverlayConfigCreate(**json.loads(req))

@router.post("/overlay")
def overlay(overlay_file:Optional[UploadFile] = None,req: OverlayConfigCreate = Depends(req_model), db: Session = Depends(get_db)):
    """
    Enqueue overlay/watermark task immediately.
    """
    # req_dict = json.loads(req)  # parse JSON string
    # req = OverlayConfigCreate(**req_dict)  # create Pydantic model
    v_repo = VideoRepository(db)  
    video = v_repo.get_video(req.video_id)

    logger.info(f"Received overlay request: {req}, file: {overlay_file.filename}")

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Read bytes from UploadFile (sync read using file.file.read)
    file_bytes = overlay_file.file.read()

    if not file_bytes:
        logger.error(f"Empty file uploaded: {overlay_file.filename}")
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # 1. Save file (sync)
    filepath = storage.save_upload(file_bytes, overlay_file.filename)

    job_id = str(uuid.uuid4())
    job_repo = JobRepository(db)

    overlay_tasks = [TaskType.TEXT_OVERLAY.value, TaskType.IMAGE_OVERLAY.value, TaskType.VIDEO_OVERLAY.value]

    task  = TaskType(req.kind).value if req.kind in overlay_tasks else None
    if not task:
        raise HTTPException(status_code=400, detail=f"Invalid overlay kind , must be one of {overlay_tasks}")
    # 1. Create job entry
    job_repo.create(
        job_id=job_id,
        video_id=video.id,
        task=task,
        status=JobStatus.PENDING.value,
        meta={}
    )
    db.commit()

    overlay = OverlayConfig(
        video_id=req.video_id,
        kind=req.kind,
        params=req.params
    )
    # 2. Save overlay/watermark config in DB
    db.add(overlay)
    db.commit()

    # 3. Enqueue Celery task
    overlay_video_task.apply_async(args=[video.id, filepath,overlay_tasks, req.params, job_id], task_id=job_id)

    return {"job_id": job_id, "video_id": video.id}
