""" Processor Celery App. """
import typing as t

from rivoli import copier
from rivoli.utils import tasks
from rivoli.utils import utils

celery = tasks.celery
app = tasks.app

#utils.configure_logger()

# Disable pyright checks due to Celery
# pyright: reportFunctionMemberAccess=false
# pyright: reportGeneralTypeIssues=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportUnknownMemberType=false

from celery.utils import log
import logging
#LOGGER = t.cast(logging.Logger, log.get_task_logger(__name__))

#LOGGER.info('TEST2')

@app.on_after_configure.connect
def setup_periodic_tasks(sender: celery.Celery, **_: t.Any):
  """ Execute the copier setup every 10 minutes. """
  sender.add_periodic_task(
      600, copier.setup_scan_tasks.s(),
      name='Copier Setup Scan Tasks')
