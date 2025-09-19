# app/api/v1/jobs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.db.session import get_db
from app.repositories.job_repo import JobRepository
from app.enums.job_status import JobStatus
from app.db.models.video import VideoVersion

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job_repo = JobRepository(db)
    job = job_repo.find(job_id)  # sync call
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "task": job.task,
        "meta": job.meta,
        "created_at": job.created_at,
    }


@router.get("/result/{job_id}")
def get_result(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.find(job_id)  # sync call
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.SUCCESS:
        raise HTTPException(
            status_code=400, detail=f"Job not completed yet (status={job.status})"
        )

    video_version_id = job.meta.get("video_version_id")
    if not video_version_id:
        raise HTTPException(status_code=500, detail="No result linked to this job")

    vv = db.get(VideoVersion, video_version_id)  # sync get
    if not vv:
        raise HTTPException(status_code=404, detail="Video version not found")

    return FileResponse(
        path=vv.filepath,
        filename=vv.filepath.split("/")[-1]
    )

