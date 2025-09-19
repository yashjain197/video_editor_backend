from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum
from backend.core.db import Base
from datetime import datetime
import enum
from pydantic import BaseModel

class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    result_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    metadata_ = Column(JSON)

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