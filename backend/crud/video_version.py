from sqlalchemy.orm import Session
from backend.models.video_version import VideoVersion

def create_video_version(db: Session, video_id: int, job_id: str = None, version_type: str = "original", quality: str = "original", filename: str = None, size: int = None, duration: float = None):
    version = VideoVersion(
        video_id=video_id,
        job_id=job_id,
        version_type=version_type,
        quality=quality,
        filename=filename,
        size=size,
        duration=duration
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

def get_versions_by_video(db: Session, video_id: int):
    return db.query(VideoVersion).filter(VideoVersion.video_id == video_id).all()

def get_best_version(db: Session, video_id: int, version_type: str = None):
    query = db.query(VideoVersion).filter(VideoVersion.video_id == video_id)
    if version_type:
        query = query.filter(VideoVersion.version_type == version_type)
    return query.order_by(VideoVersion.created_at.desc()).first()
