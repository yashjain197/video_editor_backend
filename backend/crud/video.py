from sqlalchemy.orm import Session
from backend.models.video import Video

def create_video(db: Session, filename: str, duration: float, size: int):
    video = Video(filename=filename, duration=duration, size=size)
    db.add(video)
    db.commit()
    db.refresh(video)
    return video

def get_videos(db: Session):
    return db.query(Video).all()
