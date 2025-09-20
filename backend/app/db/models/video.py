from sqlalchemy import Column, Enum, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.enums.overlay_kind import OverlayKind
from app.enums.video_quality import VideoQuality

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    size = Column(Integer)
    duration = Column(Integer)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())

    versions = relationship("VideoVersion", back_populates="original",cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="video",cascade="all, delete-orphan")
    overlays = relationship("OverlayConfig", back_populates="video")
    # watermark = relationship("Watermark", uselist=False, back_populates="video")

    # === Self-referencing relationship for trimmed videos ===
    trimmed_from_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    trimmed_videos = relationship(
        "Video",
        backref="original_video",
        remote_side=[id],
        cascade="all, delete-orphan",
        single_parent=True, 
    )


class VideoVersion(Base):
    __tablename__ = "video_versions"
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id",ondelete="CASCADE"))
    quality = Column(Enum(VideoQuality, values_callable=lambda obj: [e.value for e in obj]))  # e.g., 1080p, 720p
    filepath = Column(String, nullable=False)
    size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    original = relationship("Video", back_populates="versions")


class OverlayConfig(Base):
    __tablename__ = "overlays"
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id",ondelete="CASCADE"))
    kind = Column(Enum(OverlayKind), nullable=False)  # text/image/video
    params = Column(JSON)  # position, start, end, text, font, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="overlays")

# class Watermark(Base):
#     __tablename__ = "watermarks"
#     id = Column(Integer, primary_key=True)
#     video_id = Column(Integer, ForeignKey("videos.id",ondelete="CASCADE"))
#     filepath = Column(String, nullable=False)
#     position = Column(String, default="10:10")  # x:y or other convention
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

#     video = relationship("Video", back_populates="watermark")