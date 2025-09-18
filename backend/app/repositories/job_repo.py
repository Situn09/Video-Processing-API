# app/repositories/job_repo.py
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import json

from app.db.models import Job


class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        job_id: str,
        video_id: Optional[int],
        task: str,
        status: str = "PENDING",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """
        Create a Job row (maps to Celery task id).
        """
        try:
            job = Job(
                id=job_id,
                video_id=video_id,
                task=task,
                status=status,
                meta=meta or {}
            )
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            return job
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def update_status(
        self,
        job_id: str,
        status: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[Job]:
        """
        Update status/meta for a job. Returns updated job or None if not found.
        """
        job = await self.db.get(Job, job_id)
        if not job:
            return None

        try:
            job.status = status
            if meta is not None:
                # merge meta dictionaries (shallow merge)
                existing = job.meta or {}
                if isinstance(existing, str):
                    try:
                        existing = json.loads(existing)
                    except Exception:
                        existing = {}
                job.meta = {**existing, **meta}

            await self.db.commit()
            await self.db.refresh(job)
            return job
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def find(self, job_id: str) -> Optional[Job]:
        """
        Fetch a job by ID.
        """
        return await self.db.get(Job, job_id)
