from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_server: str
    postgres_port: int
    postgres_db: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    class Config:
        env_file = ".env"

settings = Settings()
