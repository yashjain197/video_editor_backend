from fastapi import FastAPI
from backend.api import upload, trim, overlay, jobs, quality, videos
from backend.core.config import settings
from backend.core.db import init_db

def create_app() -> FastAPI:
    app = FastAPI(
        title="Video-Processing API",
        description="Backend assignment – blank skeleton",
        version="0.1.0"
    )
    init_db()
    # register routers
    app.include_router(upload.router, prefix="/api/v1")
    app.include_router(trim.router, prefix="/api/v1")
    app.include_router(overlay.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(quality.router, prefix="/api/v1")
    app.include_router(videos.router, prefix="/api/v1")

    return app

app = create_app()
