""" Celery task app """
import celery

from rivoli import config

app = celery.Celery('processor_tasks')

app.conf.update(
  broker_url=config.get('CELERY_REDIS_URL'),
  result_backend=config.get('CELERY_REDIS_URL'),
  redis_backend_health_check_interval=30,

  task_ignore_result=True,
  task_store_errors_even_if_ignored=True,

  task_track_started=True,
  task_acks_late=True,
)
