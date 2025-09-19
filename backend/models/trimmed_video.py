from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from backend.core.db import Base
from datetime import datetime

class TrimmedVideo(Base):
    __tablename__ = "trimmed_videos"
    id = Column(Integer, primary_key=True, index=True)
    original_video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    trimmed_filename = Column(String, nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    duration = Column(Float)
    size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
