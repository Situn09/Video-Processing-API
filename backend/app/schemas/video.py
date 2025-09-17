from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class VideoOut(BaseModel):
    id: int
    filename: str
    filepath: str
    duration: Optional[int]
    size: Optional[int]
    upload_time: datetime

    class Config:
        orm_mode = True

class TrimRequest(BaseModel):
    video_id: int
    start: float
    end: float

class OverlayRequest(BaseModel):
    video_id: int
    overlays: List[Dict]  # each overlay: {kind:"text"/"image"/"video", params:{start,end,x,y,...}}
    watermark: Optional[Dict] = None
