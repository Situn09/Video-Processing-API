# app/repositories/video_repo.py
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.video import Video,VideoVersion


class VideoRepository:
    def __init__(self, db: AsyncSessionLocal):
        self.db = db

    
    async def get_video( video_id: int) -> Optional[Video]:
        res = await db.execute(select(models.Video).where(models.Video.id == video_id))
        return res.scalars().first()


    async def create(
        filename: str,
        filepath: str,
        size: Optional[int] = None,
        duration: Optional[float] = None,
    ) -> Video:
        """
        Create a Video DB record and return it.
        """
        try:
            if size is None and os.path.exists(filepath):
                size = os.path.getsize(filepath)
            v = Video(
                filename=filename,
                filepath=filepath,
                size=size,
                duration=duration,
            )
            self.db.add(v)
            await self.db.commit()
            await self.db.refresh(v)
            return v
        except SQLAlchemyError:
            await self.db.rollback()
            raise


    async def list(self, limit: int = 100, offset: int = 0) -> Optional[list[Video]]:
        res = await self.db.execute(
            select(Video).order_by(Video.upload_time.desc()).limit(limit).offset(offset)
        )
        return res.scalars().all()

    async def create_video_version(
        video_id: int,
        quality: str,
        filepath: str,
        size: Optional[int] = None,
    ) -> VideoVersion:
        """
        Insert a VideoVersion for a derived output (e.g., 1080p, 720p).
        """
        try:
            if size is None and os.path.exists(filepath):
                size = os.path.getsize(filepath)
            vv = VideoVersion(video_id=video_id, quality=quality, filepath=filepath, size=size)
            self.db.add(vv)
            await self.db.commit()
            await self.db.refresh(vv)
            return vv
        except SQLAlchemyError:
            await self.db.rollback()
            raise

