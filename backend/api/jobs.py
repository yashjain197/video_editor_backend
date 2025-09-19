from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.core.db import SessionLocal
from backend.schemas.job import JobResponse
from backend.crud.job import get_job_by_id
from backend.models.job import JobStatus
import os

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
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        result_url=job.result_url,
        created_at=job.created_at
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
