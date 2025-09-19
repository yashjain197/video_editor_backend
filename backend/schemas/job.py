from pydantic import BaseModel
from datetime import datetime

class JobResponse(BaseModel):
    job_id: str
    status: str
    result_url: str | None
    created_at: datetime
    video_id: int | None  # Added
    version_type: str | None  # Added (e.g., "trimmed", "watermarked")
