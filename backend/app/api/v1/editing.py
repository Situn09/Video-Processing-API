# app/api/v1/editing.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.db import models
from app.schemas.video import OverlayRequest
from app.services import video_service
from app.tasks.video import overlay_video_task, trim_video_task
from app.enums.job_status import JobStatus
from app.enums.task_type import TaskType
from app.repositories.job_repo import JobRepository
from app.log import logger

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


@router.post("/overlay")
def overlay(req: OverlayRequest, db: Session = Depends(get_db)):
    """
    Enqueue overlay/watermark task immediately.
    """
    video = video_service.get_video(db, req.video_id)  # sync
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    job_id = str(uuid.uuid4())
    job_repo = JobRepository(db)

    # 1. Create job entry
    job_repo.create(
        job_id=job_id,
        video_id=video.id,
        task=TaskType.OVERLAY.value,
        status=JobStatus.PENDING.value,
        meta={}
    )
    db.commit()

    # 2. Save overlay/watermark config in DB
    for ov in req.overlays:
        db.add(models.OverlayConfig(
            video_id=video.id,
            kind=ov.get("kind"),
            params=ov.get("params")
        ))

    if req.watermark:
        db.add(models.Watermark(
            video_id=video.id,
            filepath=req.watermark.get("filepath"),
            position=req.watermark.get("position", "10:10")
        ))

    db.commit()

    # 3. Enqueue Celery task
    overlay_video_task.apply_async(args=[video.id, req.overlays, req.watermark, job_id], task_id=job_id)

    return {"job_id": job_id, "video_id": video.id}
