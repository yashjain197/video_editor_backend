from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil
import os
from backend.core.db import SessionLocal
from backend.schemas.video import VideoUploadResponse
from backend.crud.video import create_video
from backend.crud.job import create_job
from backend.services.tasks import process_video_upload

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save file locally (synchronous to handle large files)
    upload_dir = "/app/videos"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create initial video entry (with placeholder metadata)
    video = create_video(db, filename=file.filename, duration=0.0, size=0)  # Placeholders, updated in task
    
    # Create job
    job = create_job(db)
    
    # Queue Celery task for metadata extraction and version creation
    process_video_upload.delay(job.job_id, video.id, file_path)
    
    return {"job_id": job.job_id}
