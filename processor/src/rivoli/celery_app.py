from rivoli import config
from rivoli import copier
from rivoli import loader
from rivoli import parser

from rivoli.utils import tasks

celery = tasks.celery
app = tasks.app



@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
  # Calls test('hello') every 10 seconds.
  sender.add_periodic_task(600.0, copier.setup_copy_tasks.s(), name='add every 10')
