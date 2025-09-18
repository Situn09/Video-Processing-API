#app/db/models/job.py
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Enum 
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.enums.task_type import TaskType
from app.enums.job_status import JobStatus

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    task = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="jobs")
