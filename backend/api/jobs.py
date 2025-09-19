from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.core.db import SessionLocal
from backend.schemas.job import JobResponse
from backend.crud.job import get_job_by_id
from backend.models.job import JobStatus
import os
from backend.crud.video_version import get_best_version
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/jobs/{job_id}/status", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch related video_id and version_type from VideoVersion (linked by job_id)
    version = get_best_version(db, video_id=None, version_type=None)  # Modify to filter by job_id if needed
    video_id = version.video_id if version else None
    version_type = version.version_type if version else "original"  # Default if no version

    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        result_url=job.result_url,
        created_at=job.created_at,
        video_id=video_id,
        version_type=version_type
    )

@router.get("/jobs/{job_id}/result")
def get_job_result(job_id: str, db: Session = Depends(get_db)):
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.completed:
        raise HTTPException(status_code=400, detail="Job not completed")
    file_path = f"/app{job.result_url}"  # e.g., /app/videos/trimmed/trimmed_uuid.mp4
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="File not found")
    return FileResponse(file_path, media_type="video/mp4", filename=os.path.basename(file_path))
