# Video Processing Backend (FastAPI)

## Requirements

- Docker + docker-compose
- ffmpeg (if running locally) built with libfreetype for drawtext
- Optional: fonts in `app/fonts` (e.g., Noto Sans for Indian languages)

## Quick start (docker)

1. Build & run:

backend command

```
uvicorn app.main:app --reload
```

redis command

```
celery -A app.tasks.celery_app.celery worker -l info -Q video_jobs --pool=solo
```
