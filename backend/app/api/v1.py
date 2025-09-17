from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.video import VideoOut, TrimRequest, OverlayRequest
from app.db import models
from app.services.storage import save_upload
from app.core.config import settings
from app.tasks.tasks import trim_task, overlay_task, transcode_multi_task
import uuid, os
from sqlalchemy import select

router = APIRouter()

@router.post("/upload", response_model=VideoOut)
async def upload_video(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await file.read()
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = save_upload(content, filename)
    size = os.path.getsize(filepath)
    # duration extraction (ffprobe) – quick way using ffprobe, shell call; for brevity store None or implement ffprobe
    duration = None
    v = models.Video(filename=file.filename, filepath=filepath, size=size, duration=duration)
    db.add(v)
    await db.commit()
    await db.refresh(v)
    # kick off transcode job for multi-quality asynchronously:
    job = transcode_multi_task.delay(filepath, Path(filepath).stem)
    # create job record
    job_record = models.Job(id=job.id, video_id=v.id, task="transcode_multi", status="PENDING", meta={})
    db.add(job_record)
    await db.commit()
    return v

@router.get("/videos", response_model=list[VideoOut])
async def list_videos(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(models.Video).order_by(models.Video.upload_time.desc()))
    items = res.scalars().all()
    return items

@router.post("/trim")
async def trim(req: TrimRequest, db: AsyncSession = Depends(get_db)):
    # validate video
    res = await db.execute(select(models.Video).where(models.Video.id == req.video_id))
    video = res.scalars().first()
    if not video:
        raise HTTPException(404, "Video not found")
    job = trim_task.delay(video.filepath, req.start, req.end)
    job_rec = models.Job(id=job.id, video_id=video.id, task="trim", status="PENDING", meta={"start": req.start, "end": req.end})
    db.add(job_rec)
    await db.commit()
    return {"job_id": job.id}

@router.post("/overlay")
async def overlay(req: OverlayRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(models.Video).where(models.Video.id == req.video_id))
    video = res.scalars().first()
    if not video:
        raise HTTPException(404, "Video not found")
    job = overlay_task.delay(video.filepath, req.overlays, req.watermark)
    job_rec = models.Job(id=job.id, video_id=video.id, task="overlay", status="PENDING", meta={})
    db.add(job_rec)
    await db.commit()
    # store overlay configs for metadata
    for ov in req.overlays:
        oc = models.OverlayConfig(video_id=video.id, kind=ov.get("kind"), params=ov.get("params"))
        db.add(oc)
    if req.watermark:
        wm = models.Watermark(video_id=video.id, filepath=req.watermark.get("path"), position=req.watermark.get("position","10:10"))
        db.add(wm)
    await db.commit()
    return {"job_id": job.id}

@router.get("/status/{job_id}")
async def status(job_id: str, db: AsyncSession = Depends(get_db)):
    # Query celery or DB job record
    from celery.result import AsyncResult
    res_db = await db.get(models.Job, job_id)
    task_info = AsyncResult(job_id)
    status = task_info.status
    # update DB record status
    if res_db:
        res_db.status = status
        await db.commit()
    return {"job_id": job_id, "status": status, "info": str(task_info.info)}

@router.get("/result/{job_id}")
async def result(job_id: str):
    from celery.result import AsyncResult
    ar = AsyncResult(job_id)
    if not ar.ready():
        return {"status": ar.status}
    res = ar.result
    # res should carry path(s)
    return res
