from typing import Union, Literal
from pydantic import BaseModel

class TextOverlayParams(BaseModel):
    text: str
    font: str
    size: int

class ImageOverlayParams(BaseModel):
    url: str
    width: int
    height: int

class VideoOverlayParams(BaseModel):
    url: str
    start_time: float
    end_time: float

class TextOverlay(BaseModel):
    kind: Literal["TEXT"]
    params: TextOverlayParams

class ImageOverlay(BaseModel):
    kind: Literal["IMAGE"]
    params: ImageOverlayParams

class VideoOverlay(BaseModel):
    kind: Literal["VIDEO"]
    params: VideoOverlayParams

OverlayConfigBase = Union[TextOverlay, ImageOverlay, VideoOverlay]
