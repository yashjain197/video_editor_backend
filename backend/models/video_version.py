from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from backend.core.db import Base
from datetime import datetime

class VideoVersion(Base):
    __tablename__ = "video_versions"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=True)
    version_type = Column(String, nullable=False)  # e.g., 'original', 'trimmed', 'overlaid', 'watermarked'
    quality = Column(String, nullable=False)  # e.g., 'original'
    filename = Column(String, nullable=False)
    size = Column(Integer)
    duration = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
