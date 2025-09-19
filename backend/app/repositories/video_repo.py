# app/repositories/video_repo.py
import os
from pathlib import Path
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from app.db.models.video import Video, VideoVersion
from app.log import logger


class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_video(self, video_id: int) -> Optional[Video]:
        """Fetch a video by ID."""
        try:
            res = self.db.execute(select(Video).where(Video.id == video_id))
            return res.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching video {video_id}: {e}", exc_info=True)
            return None
    
    # 1️⃣ Get encodings only (VideoVersion table)
    def get_video_versions(self, video_id: int) -> List[VideoVersion]:
        """Fetch only VideoVersion encodings for a video."""
        try:
            res = self.db.execute(
                select(VideoVersion).where(VideoVersion.video_id == video_id)
            )
            return res.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching video versions for {video_id}: {e}", exc_info=True)
            return []

    # 2️⃣ Get trimmed videos only (Video table self-reference)
    def get_trimmed_videos(self, video_id: int) -> List[Video]:
        """Fetch only trimmed videos of a given video."""
        try:
            res = self.db.execute(
                select(Video).where(Video.trimmed_from_id == video_id)
            )
            return res.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching trimmed videos for {video_id}: {e}", exc_info=True)
            return []

    # 3️⃣ Get everything: original video + encodings + trims (recursively)
    def get_all_versions(self, video_id: int) -> List[dict]:
        """
        Fetch:
          - Original video
          - Its VideoVersion encodings
          - Its trimmed videos (recursively, with their encodings)
        Returns a flat list of dicts for easy API use.
        """
        def collect(video: Video, collected: List[dict]):
            if not video:
                return
            collected.append({
                "type": "video",
                "id": video.id,
                "filename": video.filename,
                "filepath": video.filepath,
            })
            for v in video.versions:
                collected.append({
                    "type": "video_version",
                    "id": v.id,
                    "quality": v.quality,
                    "filepath": v.filepath,
                })
            for trimmed in video.trimmed_videos:
                collect(trimmed, collected)

        try:
            res = self.db.execute(
                select(Video)
                .options(
                    joinedload(Video.versions),
                    joinedload(Video.trimmed_videos).joinedload(Video.versions),
                )
                .where(Video.id == video_id)
            )
            video = res.scalars().first()

            collected: List[dict] = []
            collect(video, collected)
            return collected
        except SQLAlchemyError as e:
            logger.error(f"Error fetching all versions for video {video_id}: {e}", exc_info=True)
            return []

    def create(
        self,
        filename: str,
        filepath: str,
        size: Optional[int] = None,
        duration: Optional[float] = None,
        trimmed_from_id: Optional[int] = None
    ) -> Video:
        """Create a Video DB record and return it."""
        try:
            if size is None and os.path.exists(filepath):
                size = os.path.getsize(filepath)
            v = Video(
                filename=filename,
                filepath=filepath,
                size=size,
                duration=duration,
                trimmed_from_id=trimmed_from_id
            )
            self.db.add(v)
            self.db.commit()
            self.db.refresh(v)
            return v
        except SQLAlchemyError:
            logger.error("Error creating video record", exc_info=True)
            self.db.rollback()
            raise
        except Exception:
            logger.error("Unexpected error creating video record", exc_info=True)
            raise

    def list(self, limit: int = 100, offset: int = 0) -> List[Video]:
        """List videos with pagination."""
        try:
            res = self.db.execute(
                select(Video).order_by(Video.upload_time.desc()).limit(limit).offset(offset)
            )
            return res.scalars().all()
        except SQLAlchemyError:
            logger.error("Error listing videos", exc_info=True)
            return []

    def create_video_version(
        self,
        video_id: int,
        quality: str,
        filepath: str,
        size: Optional[int] = None
    ) -> VideoVersion:
        """Insert a VideoVersion for a derived output (e.g., 1080p, 720p)."""
        try:
            if size is None and os.path.exists(filepath):
                size = os.path.getsize(filepath)
            vv = VideoVersion(
                video_id=video_id,
                quality=quality,
                filepath=filepath,
                size=size
            )
            self.db.add(vv)
            self.db.commit()
            self.db.refresh(vv)
            return vv
        except SQLAlchemyError:
            logger.error("Error creating video version", exc_info=True)
            self.db.rollback()
            raise
