from pydantic import BaseModel, Field
from typing import Optional

class TextOverlayParams(BaseModel):
    text: str
    position: str = Field(..., description="x:y coordinates")
    start: float = 0
    end: Optional[float] = None
    font: Optional[str] = "Arial"

class ImageOverlayParams(BaseModel):
    src: str
    position: str = "0:0"
    start: float = 0
    end: Optional[float] = None

class VideoOverlayParams(BaseModel):
    src: str
    position: str = "0:0"
    start: float = 0
    end: Optional[float] = None
    opacity: Optional[float] = 1.0
