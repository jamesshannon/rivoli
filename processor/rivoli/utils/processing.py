""" Utils for file and record processing. """
import time

from rivoli import protos

def new_log_entry(source: str, msg: str) -> protos.ProcessingLog:
  return protos.ProcessingLog(
    source=source,
    time=int(time.time()),
    message=msg
  )
