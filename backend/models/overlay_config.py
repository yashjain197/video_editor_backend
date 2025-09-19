from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from backend.core.db import Base
from datetime import datetime

class OverlayConfig(Base):
    __tablename__ = "overlay_configs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    config = Column(JSON, nullable=False)  # Stores overlay params as JSON
    output_filename = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
