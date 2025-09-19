from sqlalchemy.orm import Session
from backend.models.overlay_config import OverlayConfig
import json

def create_overlay_config(db: Session, job_id: str, video_id: int, config: dict, output_filename: str = None):
    overlay = OverlayConfig(
        job_id=job_id,
        video_id=video_id,
        config=json.dumps(config),
        output_filename=output_filename
    )
    db.add(overlay)
    db.commit()
    db.refresh(overlay)
    return overlay

def update_overlay_config(db: Session, overlay: OverlayConfig, output_filename: str):
    overlay.output_filename = output_filename
    db.commit()
    db.refresh(overlay)
    return overlay
