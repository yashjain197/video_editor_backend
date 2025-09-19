# Video-Processing Backend (Skeleton)

## Quick start
```bash
docker-compose up --build
```

## Level 1 Implementation
- POST /api/v1/upload: Upload a video file. Extracts and stores metadata (filename, duration, size, upload_time).
- GET /api/v1/videos: List all uploaded videos with metadata.

## Level 2 Implementation (Trimming)
- POST /api/v1/trim: Queue a trim job. Body: {"video_id": 1, "start": 0, "end": 10}. Returns {"job_id": "uuid"}.
- Trimmed files are in ./videos/trimmed.

## Level 3 Implementation (Overlays & Watermark)
- POST /api/v1/overlay: Queue overlays. Body example in testing below.
- POST /api/v1/watermark: Queue watermark. Body: {"video_id": 1, "logo_path": "/videos/logo.png", "opacity": 0.5}.
- Overlaid files in ./videos/overlaid.

## Level 4 Implementation (Async Job Queue)
- All processing (upload, trim, overlay, watermark, versions) runs asynchronously using Celery + Redis.
- Returns a job_id immediately for each operation.
- GET /api/v1/jobs/{job_id}/status: Check job status.
- GET /api/v1/jobs/{job_id}/result: Download processed video if completed.

## Level 5 Implementation (Multiple Output Qualities)
- Stores "best" (original quality) versions after processing (upload, trim, overlay, watermark) in DB with type (e.g., 'trimmed', 'watermarked').
- GET /api/v1/versions/{video_id}: List all versions for a video (type, quality, filename, etc.).
- GET /api/v1/download/{video_id}/{quality}?version_type={type}: Download/transcode to specified quality (1080p, 720p, 480p) from the best/latest version (or specific type if provided). Example: /download/2/720p?version_type=trimmed.
- Transcoding is on-demand to save storage; streams MP4 directly.
- Versions stored in ./videos/versions.

