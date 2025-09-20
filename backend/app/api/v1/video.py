# app/api/v1/videos.py
import uuid
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.video import VideoOut
from app.services import video_service, storage
from app.tasks.video import add_watermark_task, generate_versions_task, process_upload_task
from app.enums.job_status import JobStatus
from app.enums.task_type import TaskType
from app.repositories.job_repo import JobRepository
from app.repositories.video_repo import VideoRepository
from app.log import logger

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post("/upload")
def upload_video(file: UploadFile, db: Session = Depends(get_db)):
    try:
        logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
        
        # Read bytes from UploadFile (sync read using file.file.read)
        file_bytes = file.file.read()

        if not file_bytes:
            logger.error(f"Empty file uploaded: {file.filename}")
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # 1. Save file (sync)
        filepath = storage.save_upload(file_bytes, file.filename)

        # 2. Create Job record immediately
        job_id = str(uuid.uuid4())
        job_repo = JobRepository(db)
        job_repo.create(
            job_id=job_id,
            video_id=None,
            task=TaskType.UPLOAD.value,
            status=JobStatus.PENDING.value,
            meta={}
        )
        db.commit()

        # 3. Enqueue Celery task
        process_upload_task.apply_async(args=[filepath, file.filename, job_id], task_id=job_id)

        # 4. Return job_id immediately
        return {"job_id": job_id, "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[VideoOut])
def list_videos(db: Session = Depends(get_db)):
    v_repo = VideoRepository(db)
    videos = v_repo.list()  # sync
    return videos


@router.post("/{video_id}/versions")
def create_versions(video_id: int, db: Session = Depends(get_db)):
    try:
        logger.info(f"Request to generate versions for video_id: {video_id}")

        # 2. Create Job record immediately
        job_id = str(uuid.uuid4())
        job_repo = JobRepository(db)
        job_repo.create(
            job_id=job_id,
            video_id=None,
            task=TaskType.TRANSCODE.value,
            status=JobStatus.PENDING.value,
            meta={}
        )
        db.commit()

        # 3. Enqueue Celery task
        generate_versions_task.apply_async(args=[video_id, job_id], task_id=job_id)

        # 4. Return job_id immediately
        return {"job_id": job_id, "video_id": video_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/versions")
def list_versions(video_id: int, db: Session = Depends(get_db)):
    v_repo = VideoRepository(db)
    return v_repo.get_video_versions(video_id)  # sync


@router.get("/{video_id}/versions/{quality}")
def download_version(video_id: int, quality: str, db: Session = Depends(get_db)):
    # try:
    #     # convert "720p" → VideoQuality.P720
    #     quality_enum = VideoQuality(quality)
    # except ValueError:
    #     raise HTTPException(status_code=400, detail=f"Invalid quality: {quality}")
    return video_service.get_version_file(video_id, quality)  # sync

@router.post("/{video_id}/watermark")
def add_watermark(video_id: int, watermark: UploadFile, db: Session = Depends(get_db)):
    try:
        logger.info(f"Received watermark file: {watermark.filename}, content_type: {watermark.content_type}")
        
        # Read bytes from UploadFile (sync read using file.file.read)
        file_bytes = watermark.file.read()

        if not file_bytes:
            logger.error(f"Empty file uploaded: {watermark.filename}")
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # 1. Save file (sync)
        filepath = storage.save_upload(file_bytes, watermark.filename)

        # 2. Create Job record immediately
        job_id = str(uuid.uuid4())
        job_repo = JobRepository(db)
        job_repo.create(
            job_id=job_id,
            video_id=None,
            task=TaskType.WATERMARK.value,
            status=JobStatus.PENDING.value,
            meta={}
        )
        db.commit()

        # 3. Enqueue Celery task
        add_watermark_task.apply_async(args=[video_id, filepath, job_id], task_id=job_id)

        # 4. Return job_id immediately
        return {"job_id": job_id, "video_id": video_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

