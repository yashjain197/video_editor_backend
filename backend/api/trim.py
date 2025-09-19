from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.db import SessionLocal
from backend.schemas.video import TrimRequest
from backend.crud.job import create_job
from backend.services.tasks import trim_video
from backend.models.video import Video  # Added this import

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/trim")
def trim_video_request(request: TrimRequest, db: Session = Depends(get_db)):
    # Validate video exists
    video = db.query(Video).filter(Video.id == request.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate timestamps
    if request.start >= request.end or request.start < 0 or request.end > video.duration:
        raise HTTPException(status_code=400, detail="Invalid start/end timestamps")
    
    # Create job
    job = create_job(db)
    
    # Queue Celery task
    trim_video.delay(job.job_id, request.video_id, request.start, request.end)
    
    return {"job_id": job.job_id}
