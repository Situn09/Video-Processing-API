from celery import Celery
from kombu import Queue
from app.core.config import settings


celery = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Load settings
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Define queues
celery.conf.task_queues = (
    Queue("video_jobs"),
)

# Route tasks to queues
celery.conf.task_routes = {
    "app.tasks.*": {"queue": "video_jobs"},
}

# Autodiscover tasks inside app.tasks
celery.autodiscover_tasks(["app.tasks"], force=True)
