""" Copier module; looks for new files and creates File record. """
import abc
import datetime
import pathlib
import re
import shutil
import time
import typing as t

from rivoli import config
from rivoli import protos
from rivoli.protobson import bson_format

from rivoli import admin_entities
from rivoli import db
from rivoli import status_scheduler
from rivoli.utils import logging
from rivoli.utils import tasks
from rivoli.utils import utils

logger = logging.get_logger(__name__)

FILES_BASE_DIR = pathlib.Path(config.get('FILES'))

@tasks.app.task
def setup_scan_tasks():
  """ Schedule a copy() task for each active partner. """
  for partner in admin_entities.get_all_partners().values():
    if partner.active:
      scan.delay(partner.id)

@tasks.app.task
def scan(partner_id: str):
  """ Search for new files for a partner and set them up for processing. """
  input_dir = FILES_BASE_DIR / 'input'
  dest_dir = FILES_BASE_DIR / 'processed'

  partner = admin_entities.get_partner(partner_id)

  logger.info('Scanning for files for Partner ID %s', partner_id)

  copier = LocalFileCopier(partner, dest_dir)
  copier.scan(input_dir)

@tasks.app.task
def copy_from_upload(orig_filename: str, temp_filename: str, partner_id: str,
    filetype_id: str):
  input_file = FILES_BASE_DIR / 'uploads' / temp_filename
  dest_dir = FILES_BASE_DIR / 'processed'

  partner = admin_entities.get_partner(partner_id)
  filetype = admin_entities.get_filetype(filetype_id)

  logger.info('Copying uploaded file for Partner ID %s', partner_id)

  copier = LocalFileCopier(partner, dest_dir)
  copier.create_file(input_file, filetype, orig_filename)

class Copier(abc.ABC):
  """ Class to look for files and prep them for loading. """
  def __init__(self, partner: protos.Partner, dest_dir: pathlib.Path):
    self.dest_dir = dest_dir
    self.partner = partner

  def create_file(self, src_file: pathlib.Path, filetype: protos.FileType,
        orig_filename: t.Optional[str] = None) -> protos.File:
    """ Move file to processed directory, create record, schedule lodading. """
    # Move the file to the destination but with a temporary file name
    # The filename will be changed right after the record is created,
    # and this approach makes orphans obvious
    tmp_file = self.dest_dir / self._file_temp_name(src_file.name)
    shutil.move(src_file, tmp_file)

    # create_file_record() only uses the src_file for parsing values and
    # setting the display File.name. Allow for overriding that. The full path +
    # name is parsed, but the full path is probably the upload directory and
    # irrelevant.
    orig_file = pathlib.Path(orig_filename) if orig_filename else src_file

    # Create the file record, which also renames the file
    file_r = self.create_file_record(orig_file, tmp_file, filetype)

    status_scheduler.next_step(file_r, filetype)

    return file_r

  def create_file_record(self, orig_file: pathlib.Path,
                  local_file: pathlib.Path, filetype: protos.FileType
                  ) -> protos.File:
    """ Create a file record with metadata and rename local file. """
    # Get a seqential ID. We do this to keep the ID small for the Record rows
    mydb = db.get_db()

    file_id = db.get_next_id('files')

    # Copy the tags from the Partner and the FileType
    tags: dict[str, str] = dict(list(self.partner.staticTags.items()) +
                                list(filetype.staticTags.items()))

    # Parse the filename for date and other tags, and override the
    # static_tags from the FileType
    date = self._parse_date(orig_file, filetype)

    # Unclear if tags should be copied into the File record or merged at
    # runtime. Runtime merge makes searching by tags much harder.
    tags.update(self._parse_tags(orig_file, filetype))
    if date:
      tags['_DATE'] = date

    file = protos.File(
      id=file_id,
      partnerId=self.partner.id,
      sizeBytes=local_file.stat().st_size,
      hash=utils.get_file_hash(local_file),
      tags=tags,
      fileDate=date,
      name=orig_file.name,
      location=str(local_file.parent),
      created=bson_format.now(),
      updated=bson_format.now(),
      status=protos.File.NEW,
      fileTypeId=filetype.id,
    )

    file.log.append(protos.ProcessingLog(
        source=protos.ProcessingLog.COPIER,
        level=protos.ProcessingLog.INFO,
        time=bson_format.now(),
        message='File Created'))

    # Get # of lines from the file
    line_count = sum(1 for _
        in open(local_file, 'r', encoding='UTF-8').readlines())
    file.stats.approximateRows = line_count

    mydb.files.insert_one(bson_format.from_proto(file))

    new_name = self._file_longterm_name(orig_file, file_id)
    local_file.rename(local_file.with_name(new_name))

    return file

  def _parse_date(self, orig_file: pathlib.Path,
      filetype: protos.FileType) -> t.Optional[str]:
    """ Parse optional "file date" from the filename. """
    if not filetype.filenameDateRegexp:
      return None

    # Evaluate the configured pattern against the filename
    matches = re.search(filetype.filenameDateRegexp, str(orig_file))
    if matches:
      groups = matches.groupdict()
      # If the captured groups include YEAR *and* MONTH *and* DAY then
      # parse those against a date parsing string.
      if 'YEAR' in groups and 'MONTH' in groups and 'DAY' in groups:
        datestr = f'{groups["YEAR"]}-{groups["MONTH"]}-{groups["DAY"]}'
        fmt = filetype.filenameDateFormat or '%Y-%m-%d'
        return datetime.datetime.strptime(datestr, fmt).date().isoformat()

    return None

  def _parse_tags(self, orig_file: pathlib.Path, filetype: protos.FileType
      ) -> dict[str, str]:
    dct: dict[str, str] = {}

    for exp in filetype.filenameTagRegexps:
      matches = re.search(exp, str(orig_file))
      if matches:
        dct.update(matches.groupdict())

    return dct

  def _file_temp_name(self, filename: str) -> str:
    return f'tmp_{int(time.time())}_{filename}.tmp'

  def _file_longterm_name(self, orig_file: pathlib.Path, file_id: int) -> str:
    # ascii85 isn't good for the filesystem, so we convert to hex?
    return f'{orig_file.stem}-{file_id}{orig_file.suffix}'

class LocalFileCopier(Copier):
  """ Copier class that scans the local filesystem for files. """
  def scan(self, input_dir: pathlib.Path):
    """ Scan source directory and import new, matching files. """
    # Create a log entry
    log = protos.CopyLog(partnerId=self.partner.id, time=bson_format.now())

    # Loop through every child in the root directory
    for child in input_dir.iterdir():
      # Currently only support files and not sub directories
      if child.is_file():
        log.files.append(self.evaluate_file(child))

    db.get_db().copylog.insert_one(bson_format.from_proto(log))


  def evaluate_file(self, file: pathlib.Path) -> protos.CopyLog.EvaluatedFile:
    """ Evaluate a file to determine if it should be copied. """
    filelog = protos.CopyLog.EvaluatedFile(
      name=file.name,
      sizeBytes=file.stat().st_size
    )

    # Has this file already been copied? If so then ignore it.
    testdb = db.get_db()
    files_filter = bson_format.get_filter_map(
        protos.File(partnerId=self.partner.id, name=file.name),
        ['partnerId', 'name'])
    resp = testdb.files.find_one(files_filter)

    if resp:
      # File has already been copied and we have a File record; update the log
      # and exit.
      filelog.resolution = protos.CopyLog.EvaluatedFile.FILE_EXISTS
      filelog.fileId = resp['_id']
      return filelog

    # This creates a lot of logspam, at least until (if?) we decide to delete
    # the file after copying
    #logger.info('Found new file: %s', file.name)

    # A partner can have multiple filetypes, and we're looking for any that are
    # available
    for filetype in self.partner.fileTypes:
      # A filetype can have multiple match expressions
      for exp in filetype.fileMatches:
        if re.fullmatch(exp, file.name):
          filelog.fileTypeId = filetype.id

          file_r = self.create_file(file, filetype)

          filelog.fileId = file_r.id
          filelog.resolution = protos.CopyLog.EvaluatedFile.COPIED

          return filelog

    # No matches
    filelog.resolution = protos.CopyLog.EvaluatedFile.NO_MATCH
    return filelog
