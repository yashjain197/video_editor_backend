from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from backend.core.db import Base
from datetime import datetime

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    duration = Column(Float)
    size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.utcnow)
