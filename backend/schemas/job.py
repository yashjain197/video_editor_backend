from pydantic import BaseModel
from datetime import datetime

class JobResponse(BaseModel):
    job_id: str
    status: str
    result_url: str | None
    created_at: datetime
    metadata: dict | None = None  # Added for errors

