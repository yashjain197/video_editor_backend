FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg postgresql-client fonts-noto wget && \
    wget -O /usr/share/fonts/truetype/krutidev.ttf https://hindityping.info/download/assets/Kruti_Dev_Fonts/KRDEV010.TTF && \
    fc-cache -f -v && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend
CMD ["celery", "-A", "backend.core.celery_app", "worker", "--loglevel=info"]
