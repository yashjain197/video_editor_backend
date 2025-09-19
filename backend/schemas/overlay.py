from pydantic import BaseModel
from typing import List, Optional

class TextOverlay(BaseModel):
    text: str
    x: int
    y: int
    start: float
    end: float
    fontcolor: Optional[str] = "white"
    fontsize: Optional[int] = 24

class ImageOverlay(BaseModel):
    image_path: str  # Relative path to image in /app/videos (upload images separately if needed)
    x: int
    y: int
    start: float
    end: float
    opacity: Optional[float] = 1.0

class VideoOverlay(BaseModel):
    video_path: str  # Relative path to overlay video
    x: int
    y: int
    start: float
    end: float

class OverlayRequest(BaseModel):
    video_id: int
    text_overlays: Optional[List[TextOverlay]] = None
    image_overlays: Optional[List[ImageOverlay]] = None
    video_overlays: Optional[List[VideoOverlay]] = None

class WatermarkRequest(BaseModel):
    video_id: int
    logo_path: str  # Relative path to logo image
    opacity: Optional[float] = 0.5
