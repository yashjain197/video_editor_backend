from pydantic import BaseModel
from datetime import datetime

class VideoUploadResponse(BaseModel):
    id: int
    filename: str
    upload_time: datetime

class VideoList(BaseModel):
    id: int
    filename: str
    duration: float | None
    size: int | None
    upload_time: datetime

class TrimRequest(BaseModel):
    video_id: int
    start: float
    end: float

class TrimmedVideoList(BaseModel):
    id: int
    original_video_id: int
    trimmed_filename: str
    start: float
    end: float
    duration: float | None
    size: int | None
    created_at: datetime

class VideoVersionList(BaseModel):
    id: int
    version_type: str
    quality: str
    filename: str
    size: int | None
    duration: float | None
    created_at: datetime
