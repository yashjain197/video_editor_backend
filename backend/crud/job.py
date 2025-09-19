import uuid
from sqlalchemy.orm import Session
from backend.models.job import Job, JobStatus

def create_job(db: Session):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, status=JobStatus.pending)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_job_by_id(db: Session, job_id: str):
    return db.query(Job).filter(Job.job_id == job_id).first()

def update_job_status(db: Session, job: Job, status: JobStatus, result_url: str = None, error_msg: str = None):
    job.status = status
    if result_url:
        job.result_url = result_url
    if error_msg:
        job.metadata_ = {"error": error_msg}
    db.commit()
    db.refresh(job)
    return job
