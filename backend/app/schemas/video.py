from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class VideoOut(BaseModel):
    id: int
    filename: str
    filepath: str
    duration: float | None = None
    size: int | None = None
    upload_time: datetime
    job_id: str | None = None

    class Config:
        from_attributes  = True

class TrimRequest(BaseModel):
    video_id: int
    start: float
    end: float


