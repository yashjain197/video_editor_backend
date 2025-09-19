from celery import shared_task
from backend.core.db import SessionLocal
from backend.crud.trimmed_video import create_trimmed_video
from backend.crud.job import get_job_by_id, update_job_status
from backend.models.job import JobStatus
from backend.models.video import Video
import subprocess
import os
import uuid

@shared_task
def process_video_upload(video_id: int):
    # TODO: ffmpeg processing
    pass

@shared_task
def trim_video(job_id: str, video_id: int, start: float, end: float):
    db = SessionLocal()
    try:
        job = get_job_by_id(db, job_id)
        if not job:
            return  # Should not happen

        update_job_status(db, job, JobStatus.processing)

        # Get original video
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            update_job_status(db, job, JobStatus.failed)
            return

        input_path = f"/app/videos/{video.filename}"
        trimmed_dir = "/app/videos/trimmed"
        os.makedirs(trimmed_dir, exist_ok=True)
        trimmed_filename = f"trimmed_{uuid.uuid4().hex}.mp4"
        output_path = f"{trimmed_dir}/{trimmed_filename}"

        # Trim with ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-i", input_path, "-ss", str(start), "-to", str(end), "-c", "copy", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stdout.decode()}")

        # Get duration and size of trimmed file
        duration_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(duration_result.stdout.decode().strip())
        size = os.path.getsize(output_path)

        # Create trimmed video entry
        create_trimmed_video(db, video_id, trimmed_filename, start, end, duration, size)

        # Update job
        result_url = f"/videos/trimmed/{trimmed_filename}"
        update_job_status(db, job, JobStatus.completed, result_url=result_url)
    except Exception as e:
        update_job_status(db, job, JobStatus.failed)
        print(f"Task error: {str(e)}")  # For logging
    finally:
        db.close()
