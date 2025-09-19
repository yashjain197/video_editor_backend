from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.core.db import SessionLocal
from backend.crud.video_version import get_best_version
import subprocess
import os
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

QUALITY_RES_MAP = {
    "1080p": "1920:1080",
    "720p": "1280:720",
    "480p": "854:480"
}

@router.get("/download/{video_id}/{quality}")
def download_video(
    video_id: int,
    quality: str,
    version_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        if quality not in QUALITY_RES_MAP:
            raise HTTPException(status_code=400, detail="Invalid quality")

        best_version = get_best_version(db, video_id, version_type)
        if not best_version:
            raise HTTPException(status_code=404, detail="No matching video version found")

        input_path = f"/app/videos/versions/{best_version.filename}"
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="Video file not found")

        res = QUALITY_RES_MAP[quality]
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", f"scale={res}:force_original_aspect_ratio=decrease,pad={res}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-movflags", "frag_keyframe+empty_moov", "-f", "mp4",
            "pipe:1"
        ]

        def generate():
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                output = process.stdout.read(4096)
                if not output:
                    break
                yield output
            stderr = process.stderr.read().decode()
            if process.returncode != 0:
                logger.error(f"FFmpeg error during transcode: {stderr}")
            process.stdout.close()

        return StreamingResponse(generate(), media_type="video/mp4", headers={"Content-Disposition": f"attachment; filename={quality}_{best_version.version_type}_{best_version.filename}"})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error downloading video {video_id} in {quality}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing download")
