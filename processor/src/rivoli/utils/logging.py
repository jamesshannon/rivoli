""" Logging setup. """
import logging
import typing as t

from celery.app.log import TaskFormatter
from celery.utils import log

def get_logger(name: str) -> logging.Logger:
  """ Get a pre-configured Celery logger. """
  # NB: Celery has its own logging configuration

  base_logger = logging.getLogger()
  if not base_logger.handlers:
    # This is used outside of a celery task context
    sh = logging.StreamHandler()
    sh.setFormatter(TaskFormatter('%(asctime)s - %(task_id)s - %(task_name)s - %(name)s - %(levelname)s - %(message)s'))
    sh.setLevel(logging.DEBUG)

    base_logger.setLevel(logging.DEBUG)
    base_logger.addHandler(sh)

  logger = t.cast(logging.Logger, log.get_task_logger(name))
  logger.setLevel(logging.DEBUG)
  return logger

class CeleryTaskFormatter(logging.Formatter):
  """ logging.Formatter which will include Celery context, if relevant. """
  def __init__(self, *args: t.Any, **kwargs: t.Any):
    super().__init__(*args, **kwargs)
    try:
      # pylint: disable=import-outside-toplevel
      # pyright: reportMissingTypeStubs=false
      from celery._state import get_current_task
      self.get_current_task = get_current_task
    except ImportError:
      self.get_current_task = lambda: None

  def format(self, record: logging.LogRecord):
    task = self.get_current_task()
    if task and task.request:
      record.__dict__.update(task_id=task.request.id, task_name=task.name)
    else:
      record.__dict__.setdefault('task_name', '')
      record.__dict__.setdefault('task_id', '')
    return super().format(record)
