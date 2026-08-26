from celery import Celery

from backend.core.config import get_settings
from backend.workers.queues import CELERY_QUEUES

settings = get_settings()

celery_app = Celery(
    "deepresearch",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.workers.tasks"],
)

celery_app.conf.update(
    task_queues=CELERY_QUEUES,
    task_default_queue="graph_q",
    task_track_started=True,
    worker_prefetch_multiplier=1,  # long-running graph tasks: don't hoard work
    task_acks_late=True,  # crash mid-run -> task redelivered, checkpoint resumes it
    result_expires=86400,
)
