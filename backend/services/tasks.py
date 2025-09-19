from celery import shared_task
from backend.core.db import SessionLocal
from backend.crud.trimmed_video import create_trimmed_video
from backend.crud.job import get_job_by_id, update_job_status
from backend.models.job import JobStatus
from backend.models.video import Video
import subprocess
import os
import uuid
import json
import tempfile
from backend.crud.overlay import update_overlay_config
from backend.models.overlay_config import OverlayConfig
from celery.utils.log import get_task_logger
from backend.crud.video_version import create_video_version
import shutil 

logger = get_task_logger(__name__)

@shared_task
def process_video_upload(job_id: str, video_id: int, file_path: str):
    db = SessionLocal()
    try:
        job = get_job_by_id(db, job_id)
        if not job:
            return

        update_job_status(db, job, JobStatus.processing)

        # Get size
        size = os.path.getsize(file_path)
        
        # Get duration using ffprobe
        duration_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        if duration_result.returncode != 0:
            raise Exception(f"FFmpeg error: {duration_result.stdout.decode()}")
        duration = float(duration_result.stdout.decode().strip())

        # Update video entry with metadata
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise Exception("Video not found")
        video.duration = duration
        video.size = size
        db.commit()
        db.refresh(video)

        # Create original video version (copy file to versions dir)
        versions_dir = "/app/videos/versions"
        os.makedirs(versions_dir, exist_ok=True)
        version_filename = f"original_{uuid.uuid4().hex}.mp4"
        version_path = f"{versions_dir}/{version_filename}"
        shutil.copy(file_path, version_path)  # Copy to versions for consistency

        create_video_version(db, video_id=video_id, job_id=job_id, version_type="original", filename=version_filename, size=size, duration=duration)

        result_url = f"/videos/versions/{version_filename}"
        update_job_status(db, job, JobStatus.completed, result_url=result_url)
    except Exception as e:
        update_job_status(db, job, JobStatus.failed, error_msg=str(e))
        print(f"Task error: {str(e)}")
    finally:
        db.close()

@shared_task
def trim_video(job_id: str, video_id: int, start: float, end: float):
    db = SessionLocal()
    try:
        job = get_job_by_id(db, job_id)
        if not job:
            return

        update_job_status(db, job, JobStatus.processing)

        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            update_job_status(db, job, JobStatus.failed)
            return

        input_path = f"/app/videos/{video.filename}"
        versions_dir = "/app/videos/versions"
        os.makedirs(versions_dir, exist_ok=True)
        trimmed_filename = f"trimmed_{uuid.uuid4().hex}.mp4"
        output_path = f"{versions_dir}/{trimmed_filename}"

        result = subprocess.run(
            ["ffmpeg", "-i", input_path, "-ss", str(start), "-to", str(end), "-c", "copy", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stdout.decode()}")

        duration_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(duration_result.stdout.decode().strip())
        size = os.path.getsize(output_path)

        # Create trimmed entry (existing)
        create_trimmed_video(db, video_id, trimmed_filename, start, end, duration, size)

        # Create video version
        create_video_version(db, video_id=video_id, job_id=job_id, version_type="trimmed", filename=trimmed_filename, size=size, duration=duration)

        result_url = f"/videos/versions/{trimmed_filename}"
        update_job_status(db, job, JobStatus.completed, result_url=result_url)
    except Exception as e:
        update_job_status(db, job, JobStatus.failed)
        print(f"Task error: {str(e)}")
    finally:
        db.close()

@shared_task
def apply_overlays(job_id: str, video_id: int):
    db = SessionLocal()
    try:
        job = get_job_by_id(db, job_id)
        update_job_status(db, job, JobStatus.processing)

        overlay = db.query(OverlayConfig).filter(OverlayConfig.job_id == job_id).first()
        config = json.loads(overlay.config)

        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise Exception("Video not found")

        input_path = f"/app/videos/{video.filename}"
        versions_dir = "/app/videos/versions"
        os.makedirs(versions_dir, exist_ok=True)
        output_filename = f"overlaid_{uuid.uuid4().hex}.mp4"
        output_path = f"{versions_dir}/{output_filename}"

        # Prepare FFmpeg command
        cmd = ["ffmpeg"]
        inputs = ["-i", input_path]
        filter_complex = []
        current_stream = "[0:v]"
        input_index = 1
        temp_files = []

        # Text overlays
        temp_idx = 0
        for text in config.get('text_overlays', []):
            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False) as temp_file:
                temp_file.write(text['text'])
                temp_text_file = temp_file.name
            temp_files.append(temp_text_file)

            enable = f"between(t,{text['start']},{text['end']})"
            drawtext_filter = f"{current_stream} drawtext=textfile='{temp_text_file}':x={text['x']}:y={text['y']}:fontcolor={text.get('fontcolor', 'white')}:fontsize={text.get('fontsize', 24)}:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:enable='{enable}' [txt{temp_idx}]"
            filter_complex.append(drawtext_filter)
            current_stream = f"[txt{temp_idx}]"
            temp_idx += 1

        # Image overlays
        for image in config.get('image_overlays', []):
            image_path = image['image_path']
            inputs.extend(["-i", image_path])
            enable = f"between(t,{image['start']},{image['end']})"
            opacity = image.get('opacity', 1.0)
            if opacity < 1.0:
                overlay_filter = f"[{input_index}:v] colorchannelmixer=aa={opacity} [imgovl{input_index}]; {current_stream}[imgovl{input_index}] overlay={image['x']}:{image['y']}:enable='{enable}' [img{input_index}]"
            else:
                overlay_filter = f"{current_stream}[{input_index}:v] overlay={image['x']}:{image['y']}:enable='{enable}' [img{input_index}]"
            filter_complex.append(overlay_filter)
            current_stream = f"[img{input_index}]"
            input_index += 1

        # Video overlays
        for video_ovl in config.get('video_overlays', []):
            video_path = video_ovl['video_path']
            inputs.extend(["-i", video_path])
            enable = f"between(t,{video_ovl['start']},{video_ovl['end']})"
            overlay_filter = f"{current_stream}[{input_index}:v] overlay={video_ovl['x']}:{video_ovl['y']}:enable='{enable}' [vid{input_index}]"
            filter_complex.append(overlay_filter)
            current_stream = f"[vid{input_index}]"
            input_index += 1

        # Finalize filter_complex
        if filter_complex:
            filter_str = ";".join(filter_complex)
            cmd += inputs + ["-filter_complex", filter_str, "-map", current_stream, "-map", "0:a", "-c:v", "libx264", "-c:a", "copy", output_path]
        else:
            cmd += inputs + ["-c:v", "copy", "-c:a", "copy", output_path]

        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_output = result.stderr + "\n" + result.stdout
            raise Exception(f"FFmpeg failed: {error_output}")

        # Cleanup temp files
        for temp_file in temp_files:
            os.remove(temp_file)

        # Create video version
        size = os.path.getsize(output_path)
        duration_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(duration_result.stdout.decode().strip())

        create_video_version(db, video_id=video_id, job_id=job_id, version_type="overlaid", filename=output_filename, size=size, duration=duration)

        update_overlay_config(db, overlay, output_filename)
        result_url = f"/videos/versions/{output_filename}"
        update_job_status(db, job, JobStatus.completed, result_url=result_url)
    except Exception as e:
        update_job_status(db, job, JobStatus.failed, error_msg=str(e))
        print(f"Task error: {str(e)}")
    finally:
        db.close()

@shared_task
def apply_watermark(job_id: str, video_id: int):
    db = SessionLocal()
    try:
        job = get_job_by_id(db, job_id)
        update_job_status(db, job, JobStatus.processing)

        overlay = db.query(OverlayConfig).filter(OverlayConfig.job_id == job_id).first()
        config = json.loads(overlay.config)

        video = db.query(Video).filter(Video.id == video_id).first()
        input_path = f"/app/videos/{video.filename}"
        logo_path = config['logo_path']
        opacity = config['opacity']
        start = config['start']
        end = config['end']
        x = config['x']
        y = config['y']

        versions_dir = "/app/videos/versions"
        os.makedirs(versions_dir, exist_ok=True)
        output_filename = f"watermarked_{uuid.uuid4().hex}.mp4"
        output_path = f"{versions_dir}/{output_filename}"

        # FFmpeg command: Scale logo to small size (max 100px width), apply opacity, position, and timing
        enable = f"between(t,{start},{end})"
        cmd = [
            "ffmpeg", "-i", input_path, "-i", logo_path,
            "-filter_complex", f"[1:v]scale=100:-1[scaled]; [scaled]format=yuva444p,colorchannelmixer=aa={opacity}[wm]; [0:v][wm]overlay={x}:{y}:enable='{enable}'",
            "-c:v", "libx264", "-c:a", "copy", output_path
        ]

        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_output = result.stderr + "\n" + result.stdout
            raise Exception(f"FFmpeg failed: {error_output}")

        # Create video version
        size = os.path.getsize(output_path)
        duration_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(duration_result.stdout.decode().strip())

        create_video_version(db, video_id=video_id, job_id=job_id, version_type="watermarked", filename=output_filename, size=size, duration=duration)

        update_overlay_config(db, overlay, output_filename)
        result_url = f"/videos/versions/{output_filename}"
        update_job_status(db, job, JobStatus.completed, result_url=result_url)
    except Exception as e:
        update_job_status(db, job, JobStatus.failed, error_msg=str(e))
        print(f"Error: {str(e)}")
    finally:
        db.close()

