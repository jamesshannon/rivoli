""" Processor Celery App. """
import typing as t

from rivoli import copier
from rivoli.utils import tasks

celery = tasks.celery
app = tasks.app

# Disable pyright checks due to Celery
# pyright: reportFunctionMemberAccess=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportUnknownMemberType=false

@app.on_after_configure.connect
def setup_periodic_tasks(sender: celery.Celery, **_: t.Any):
  """ Execute the copier scan tasks every 10 minutes. """
  sender.add_periodic_task(
      600, copier.setup_scan_tasks.s(),
      name='Copier Setup Scan Tasks')
