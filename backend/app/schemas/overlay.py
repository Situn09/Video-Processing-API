
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel
from app.enums.overlay_kind import OverlayKind
from app.schemas.overlay_params import ImageOverlayParams, TextOverlayParams, VideoOverlayParams


class OverlayParams(BaseModel):
    text: Optional[str] = None  # for text overlays
    position: str  # e.g., "top-left", "center", etc.
    start_time: float = 0.0  # in seconds
    end_time: float = None  # in seconds, None means till end of video

class OverlayConfigCreate(BaseModel):
    video_id: int
    kind: OverlayKind
    params: OverlayParams  # will be validated before save

class OverlayConfigRead(BaseModel):
    id: int
    video_id: int
    kind: OverlayKind
    params: OverlayParams
    created_at: datetime

    class Config:
        from_attributes = True

def validate_overlay(kind: OverlayKind, params: dict) -> dict:
    if kind == OverlayKind.TEXT:
        return TextOverlayParams(**params).dict()
    elif kind == OverlayKind.IMAGE:
        return ImageOverlayParams(**params).dict()
    elif kind == OverlayKind.VIDEO:
        return VideoOverlayParams(**params).dict()
    else:
        raise ValueError(f"Unsupported overlay kind: {kind}")

