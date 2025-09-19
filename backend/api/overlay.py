from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.core.db import SessionLocal
from backend.crud.job import create_job
from backend.services.tasks import apply_overlays
from backend.models.video import Video
from backend.crud.overlay import create_overlay_config
import os
import uuid
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/overlay")
def overlay_video_request(
    video_id: int = Form(...),
    text_overlays_json: Optional[str] = Form(None),  # JSON string for text overlays (array of objects)
    image_files: List[UploadFile] = File(None),  # Uploaded image files
    image_params_json: Optional[str] = Form(None),  # JSON string for image params (array matching image_files)
    video_files: List[UploadFile] = File(None),  # Uploaded video files
    video_params_json: Optional[str] = Form(None),  # JSON string for video params (array matching video_files)
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    job = create_job(db)

    # Directory for temporary uploads
    upload_dir = "/app/videos"
    os.makedirs(upload_dir, exist_ok=True)

    # Process text overlays (from JSON string)
    text_overlays = json.loads(text_overlays_json) if text_overlays_json else []

    # Process image overlays
    image_overlays = []
    image_params = json.loads(image_params_json) if image_params_json else []
    if len(image_files) != len(image_params):
        raise HTTPException(status_code=400, detail="Number of image files must match image params")
    for i, file in enumerate(image_files or []):
        file_ext = os.path.splitext(file.filename)[1]
        image_path = f"{upload_dir}/overlay_image_{uuid.uuid4().hex}{file_ext}"
        with open(image_path, "wb") as buffer:
            buffer.write(file.file.read())
        param = image_params[i]
        image_overlays.append({
            "image_path": image_path,
            "x": param.get("x", 100),
            "y": param.get("y", 100),
            "start": param.get("start", 0),
            "end": param.get("end", 10),
            "opacity": param.get("opacity", 1.0)
        })

    # Process video overlays
    video_overlays = []
    video_params = json.loads(video_params_json) if video_params_json else []
    if len(video_files) != len(video_params):
        raise HTTPException(status_code=400, detail="Number of video files must match video params")
    for i, file in enumerate(video_files or []):
        file_ext = os.path.splitext(file.filename)[1]
        video_path = f"{upload_dir}/overlay_video_{uuid.uuid4().hex}{file_ext}"
        with open(video_path, "wb") as buffer:
            buffer.write(file.file.read())
        param = video_params[i]
        video_overlays.append({
            "video_path": video_path,
            "x": param.get("x", 200),
            "y": param.get("y", 200),
            "start": param.get("start", 0),
            "end": param.get("end", 10)
        })

    # Create config
    config = {
        "text_overlays": text_overlays,
        "image_overlays": image_overlays,
        "video_overlays": video_overlays
    }

    create_overlay_config(db, job.job_id, video_id, config)

    apply_overlays.delay(job.job_id, video_id)

    return {"job_id": job.job_id}
