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
from backend.crud.overlay import create_overlay_config, update_overlay_config
from backend.crud.job import get_job_by_id, update_job_status
from backend.models.job import JobStatus
from backend.models.overlay_config import OverlayConfig
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)  # For logging inside the task

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
        overlaid_dir = "/app/videos/overlaid"
        os.makedirs(overlaid_dir, exist_ok=True)
        output_filename = f"overlaid_{uuid.uuid4().hex}.mp4"
        output_path = f"{overlaid_dir}/{output_filename}"

        # Prepare FFmpeg command
        cmd = ["ffmpeg"]
        inputs = ["-i", input_path]  # Input 0: main video
        filter_complex = []
        current_stream = "[0:v]"  # Start with main video stream
        input_index = 1  # Next input index after main video
        temp_files = []  # For text temp files

        # Text overlays (applied to current stream)
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

        # If there are filters, finalize with [outv] label
        if filter_complex:
            filter_complex.append(f"{current_stream} null [outv]")  # Final label for video
            filter_str = ";".join(filter_complex)
            cmd += inputs + ["-filter_complex", filter_str, "-map", "[outv]", "-map", "0:a", "-c:v", "libx264", "-c:a", "copy", output_path]
        else:
            cmd += inputs + ["-c:v", "copy", "-c:a", "copy", output_path]

        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_output = result.stderr + "\n" + result.stdout
            raise Exception(f"FFmpeg failed: {error_output}")

        # Cleanup temp text files
        for temp_file in temp_files:
            os.remove(temp_file)

        update_overlay_config(db, overlay, output_filename)
        result_url = f"/videos/overlaid/{output_filename}"
        update_job_status(db, job, JobStatus.completed, result_url=result_url)
    except Exception as e:
        update_job_status(db, job, JobStatus.failed, error_msg=str(e))
        print(f"Task error: {str(e)}")  # For Celery logs
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

        overlaid_dir = "/app/videos/overlaid"
        os.makedirs(overlaid_dir, exist_ok=True)
        output_filename = f"watermarked_{uuid.uuid4().hex}.mp4"
        output_path = f"{overlaid_dir}/{output_filename}"

        # FFmpeg command for watermark (bottom-right, semi-transparent)
        cmd = [
            "ffmpeg", "-i", input_path, "-i", logo_path,
            "-filter_complex", f"[1:v]format=yuva444p, colorchannelmixer=aa={opacity}[wm]; [0:v][wm]overlay=main_w-overlay_w-10:main_h-overlay_h-10",
            "-c:v", "libx264", output_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stdout.decode()}")

        update_overlay_config(db, overlay, output_filename)
        result_url = f"/videos/overlaid/{output_filename}"
        update_job_status(db, job, JobStatus.completed, result_url=result_url)
    except Exception as e:
        update_job_status(db, job, JobStatus.failed)
        print(f"Error: {str(e)}")
    finally:
        db.close()