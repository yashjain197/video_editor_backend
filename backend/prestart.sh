#!/bin/sh
until PGPASSWORD=$POSTGRES_PASSWORD pg_isready -h "$POSTGRES_SERVER" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Postgres is unavailable – sleeping"
  sleep 1
done
echo "Postgres is up – starting app"
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
