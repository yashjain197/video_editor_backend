from fastapi import FastAPI
from backend.api import upload, trim, overlay, jobs, quality, videos, download, versions, watermark
from backend.core.config import settings
from backend.core.db import init_db
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
logger = logging.getLogger(__name__)
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
    app.include_router(download.router, prefix="/api/v1")
    app.include_router(versions.router, prefix="/api/v1")
    app.include_router(watermark.router, prefix="/api/v1")
    # Global exception handler for unhandled errors (logs and returns details)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {str(exc)}", exc_info=True)  # Logs traceback
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error - Check server logs"})

    # Handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    # Handler for HTTP exceptions (customize 404, etc.)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.info(f"HTTP error {exc.status_code}: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return app

app = create_app()
