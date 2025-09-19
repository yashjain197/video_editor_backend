from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from backend.core.db import SessionLocal
from backend.crud.job import create_job
from backend.services.tasks import apply_watermark
from backend.models.video import Video
from backend.crud.overlay import create_overlay_config
import os
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/watermark")
def watermark_video_request(
    video_id: int = Form(...),
    start: Optional[float] = Form(None),
    end: Optional[float] = Form(None),
    x: Optional[int] = Form(None),  # Optional, defaults to bottom-right
    y: Optional[int] = Form(None),  # Optional, defaults to bottom-right
    opacity: Optional[float] = Form(0.5),
    file: UploadFile = File(...),  # Logo image upload
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Default timestamps to full video if not provided
    start = start or 0
    end = end or video.duration

    # Default position to bottom-right (using FFmpeg variables)
    x_str = str(x) if x is not None else "main_w - overlay_w - 10"
    y_str = str(y) if y is not None else "main_h - overlay_h - 10"

    # Save uploaded logo
    upload_dir = "/app/videos/watermarks"
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    logo_filename = f"logo_{uuid.uuid4().hex}{file_ext}"
    logo_path = os.path.join(upload_dir, logo_filename)
    with open(logo_path, "wb") as buffer:
        buffer.write(file.file.read())

    # Create config
    config = {
        "logo_path": logo_path,
        "start": start,
        "end": end,
        "x": x_str,
        "y": y_str,
        "opacity": opacity
    }

    job = create_job(db)
    create_overlay_config(db, job.job_id, video_id, config)
    apply_watermark.delay(job.job_id, video_id)

    return {"job_id": job.job_id}
