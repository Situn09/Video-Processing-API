from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    size = Column(Integer)
    duration = Column(Integer)  # seconds
    upload_time = Column(DateTime(timezone=True), server_default=func.now())

    versions = relationship("VideoVersion", back_populates="original")
    jobs = relationship("Job", back_populates="video")
    overlays = relationship("OverlayConfig", back_populates="video")
    watermark = relationship("Watermark", uselist=False, back_populates="video")

class VideoVersion(Base):
    __tablename__ = "video_versions"
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    quality = Column(String)  # '1080p', '720p', '480p', 'original', 'trimmed'
    filepath = Column(String, nullable=False)
    size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    original = relationship("Video", back_populates="versions")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)  # UUID or Celery task id
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    task = Column(String)
    status = Column(String, default="PENDING")
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="jobs")

class OverlayConfig(Base):
    __tablename__ = "overlays"
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    kind = Column(String)  # text/image/video
    params = Column(JSON)  # position, start, end, text, font, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="overlays")

class Watermark(Base):
    __tablename__ = "watermarks"
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    filepath = Column(String, nullable=False)
    position = Column(String, default="10:10")  # x:y or other convention
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="watermark")
