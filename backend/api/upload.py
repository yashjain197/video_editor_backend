from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil
import os
import subprocess
from backend.core.db import SessionLocal
from backend.schemas.video import VideoUploadResponse
from backend.crud.video import create_video

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", response_model=VideoUploadResponse)
def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save file locally
    upload_dir = "/app/videos"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get size
    size = os.path.getsize(file_path)
    
    # Get duration using ffprobe
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(result.stdout.decode().strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting duration: {str(e)}")
    
    # Store in DB
    video = create_video(db, filename=file.filename, duration=duration, size=size)
    
    return VideoUploadResponse(id=video.id, filename=video.filename, upload_time=video.upload_time)
