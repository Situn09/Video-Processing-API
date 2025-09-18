from pydantic import BaseModel
from typing import Union
from app.enums.overlay_kind import OverlayKind
from app.schemas.overlay_params import (
    TextOverlayParams,
    ImageOverlayParams,
    VideoOverlayParams,
)

class OverlayConfigBase(BaseModel):
    kind: OverlayKind
    params: Union[TextOverlayParams, ImageOverlayParams, VideoOverlayParams]

class OverlayConfigCreate(OverlayConfigBase):
    video_id: int

class OverlayConfigRead(OverlayConfigBase):
    id: int
    video_id: int

    class Config:
        from_attributes  = True
