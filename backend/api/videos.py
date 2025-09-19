from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.core.db import SessionLocal
from backend.schemas.video import VideoList
from backend.crud.video import get_videos

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/videos", response_model=List[VideoList])
def list_videos(db: Session = Depends(get_db)):
    videos = get_videos(db)
    return [VideoList(id=v.id, filename=v.filename, duration=v.duration, size=v.size, upload_time=v.upload_time) for v in videos]
