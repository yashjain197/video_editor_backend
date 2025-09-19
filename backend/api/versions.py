from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.core.db import SessionLocal
from backend.crud.video_version import get_versions_by_video
from backend.schemas.video import VideoVersionList  # Create this schema if needed
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/versions/{video_id}", response_model=List[VideoVersionList])
def list_versions(video_id: int, db: Session = Depends(get_db)):
    try:
        versions = get_versions_by_video(db, video_id)
        if not versions:
            raise HTTPException(status_code=404, detail="No versions found for this video")
        return versions
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error listing versions for video {video_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving versions")

