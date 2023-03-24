""" Celery task app """

import celery

app = celery.Celery('processor_tasks')

app.conf.update(
  broker_url= 'redis://localhost:6379/0',
  result_backend='redis://localhost:6379/0',
  redis_backend_health_check_interval=30,

  task_ignore_result=True,
  task_store_errors_even_if_ignored=True,

  task_track_started=True,
  task_acks_late=True,
)
