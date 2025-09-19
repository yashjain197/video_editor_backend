from sqlalchemy.orm import Session
from backend.models.trimmed_video import TrimmedVideo

def create_trimmed_video(db: Session, original_video_id: int, trimmed_filename: str, start: float, end: float, duration: float, size: int):
    trimmed = TrimmedVideo(
        original_video_id=original_video_id,
        trimmed_filename=trimmed_filename,
        start=start,
        end=end,
        duration=duration,
        size=size
    )
    db.add(trimmed)
    db.commit()
    db.refresh(trimmed)
    return trimmed
