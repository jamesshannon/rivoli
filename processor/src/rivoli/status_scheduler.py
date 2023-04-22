""" Moves Files between statuses, schedules next steps as needed. """
from rivoli import db
from rivoli import admin_entities
from rivoli import protos
from rivoli.protobson import bson_format
from rivoli.utils import logging
from rivoli.utils import tasks

# Individual processor steps
from rivoli import loader
from rivoli import parser
from rivoli import validator
from rivoli import uploader
from rivoli import reporter

logger = logging.get_logger(__name__)

# Disable pyright checks for Celery
# pyright: reportFunctionMemberAccess=false
# pyright: reportUnknownMemberType=false

@tasks.app.task
def next_step_id(file_id: int) -> None:
  """ Move file to next step using just the File ID.
  This will be almost exclusively used as a Celery task (called from the front-
  end); otherwise the File and FileType should be available.
  """
  file, _, filetype = admin_entities.get_file_entities(file_id)
  next_step(file, filetype)

def next_step(file: protos.File, file_type: protos.FileType) -> None:
  """ Move file to the next step.
  For the most part this will simply create a Celery task based on the current
  status, but the task might differ based on current status + FileType
  configuration.
  """
  if file.status == protos.File.NEW:
    # File was just created
    _next_step_new(file)

  elif file.status == protos.File.LOADED:
    _next_step_loaded(file)

  elif file.status == protos.File.PARSED:
    _next_step_parsed(file)

  elif file.status in (protos.File.VALIDATED, protos.File.APPROVED_TO_UPLOAD):
    _next_step_validated(file, file_type)

  elif file.status in (protos.File.UPLOADED, ):
    _next_step_uploaded(file, file_type)

  elif file.status in (protos.File.WAITING_APPROVAL_TO_UPLOAD):

  else:
    logger.error('File (ID %s) status (%s) does not have a next step',
        file.id, file.status)

def _log_next_step(file: protos.File, step: str) -> None:
  logger.info('Scheduling %s for File ID %s', step, file.id)

def _next_step_new(file: protos.File) -> None:
  """ Schedule file loading. """
  _log_next_step(file, 'loading')
  loader.load_from_id.delay(file.id)

def _next_step_loaded(file: protos.File) -> None:
  """ Schedule record parsing. """
  _log_next_step(file, 'parsing')
  parser.parse.delay(file.id)

def _next_step_parsed(file: protos.File) -> None:
  """ Schedule record validation. """
  _log_next_step(file, 'validation')
  validator.validate.delay(file.id)

def _next_step_validated(file: protos.File, file_type: protos.FileType) -> None:
  """ Schedule record uploading, or pause. """
  # decide what to do next.
  # aggregating if there are aggregation steps
  # if not, then waiting for approval if that flag is set and there are >0 errors
  # if not, then upload if upload is configured
  # if not, then direct to completed

  # Always start uploading if the status is APPROVED
  if file.status == protos.File.APPROVED_TO_UPLOAD:
    _log_next_step(file, 'uploading')
    uploader.upload.delay(file.id)
    return

  has_errors = file.stats.validatedRecordsError > 0

  # No explicit approval -- check if approval is needed
  if (file_type.requireUploadReview == file_type.ALWAYS
      or (file_type.requireUploadReview == file_type.ON_ERRORS and has_errors)):
    # Manual review is required. Set to appropriate status but don't schedule
    # anything.
    logger.info('Updating status of File ID %s to WAITING_APPROVAL_TO_UPLOAD',
        file.id)
    _update_file_status(file, protos.File.WAITING_APPROVAL_TO_UPLOAD)
    # Send a notification

    return

  _log_next_step(file, 'uploading')
  uploader.upload.delay(file.id)

def _next_step_uploaded(file: protos.File, file_type: protos.FileType) -> None:
  # Decide what to do next. One (or more) reports? Otherwise completed
  # Eventually support a "needs manual post-upload review" status
  # How to eventually transition to completed when all reports are done?

  _log_next_step(file, 'reporting')
  _update_file_status(file, protos.File.REPORTING)

  reporter.report.delay(file.id, file_type.id)

def _next_step_reporting(file: protos.File, file_type: protos.FileType) -> None:
  # There could be many reports and so we need to determine if they've all
  # completed (successfully) and, if so, what the next steps are
  pass
def _update_file_status(file: protos.File, status: protos.File.Status) -> None:
  # Probably want to add a File.log shortcut here.
  file.status = status
  db.get_db().files.update_one(*bson_format.get_update_args(file, ['status']))

