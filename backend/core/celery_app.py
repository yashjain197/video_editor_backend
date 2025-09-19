from celery import Celery
from backend.core.config import settings

celery_app = Celery(
    "video_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.services.tasks"]
)
