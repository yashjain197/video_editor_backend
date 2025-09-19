# Video-Processing Backend (Skeleton)

## Quick start
```bash
docker compose up --build
```

## Level 1 Implementation
- POST /api/v1/upload: Upload a video file. Extracts and stores metadata (filename, duration, size, upload_time).
- GET /api/v1/videos: List all uploaded videos with metadata.

### Testing Level 1
- Use FastAPI docs at http://localhost:8000/docs.
- For upload, send a multipart/form-data request with a video file.
- Videos are stored in ./videos folder locally.

## Level 2 Implementation (Async Trimming)
- POST /api/v1/trim: Queue a trim job. Body: {"video_id": 1, "start": 0, "end": 10}. Returns {"job_id": "uuid"}.
- GET /api/v1/jobs/{job_id}/status: Check job status.
- GET /api/v1/jobs/{job_id}/result: Download trimmed video if completed.
- Trimmed files are in ./videos/trimmed.

## Level 3 Implementation (Async Overlays & Watermark)
- POST /api/v1/overlay: Queue overlays. Body example in testing below.
- POST /api/v1/watermark: Queue watermark. Body: {"video_id": 1, "logo_path": "/videos/logo.png", "opacity": 0.5}.
- Use /jobs/{job_id}/status and /result for tracking/download.
- Supports Hindi text (e.g., "नमस्ते" in text overlay).
- Overlaid files in ./videos/overlaid.

## Level 5 Implementation (Multiple Output Qualities)
- Stores "best" (original quality) versions after processing (upload, trim, overlay, watermark) in DB with type (e.g., 'trimmed', 'watermarked').
- GET /api/v1/versions/{video_id}: List all versions for a video (type, quality, filename, etc.).
- GET /api/v1/download/{video_id}/{quality}?version_type={type}: Download/transcode to specified quality (1080p, 720p, 480p) from the best/latest version (or specific type if provided). Example: /download/2/720p?version_type=trimmed.
- Transcoding is on-demand to save storage; streams MP4 directly.
- Versions stored in ./videos/versions.