""" Copier classes """
import abc
import datetime
import pathlib
import re
import shutil
import time
import typing as t

import bson

from rivoli import protos
from rivoli.protobson import bson_format

from rivoli import admin_entities
from rivoli import db
from rivoli import record_processor
from rivoli.utils import processing
from rivoli.utils import tasks
from rivoli.utils import utils

@tasks.app.task
def setup_scan_tasks():
  """ Schedule a copy() task for each active partner. """
  for partner in admin_entities.get_all_partners().values():
    if partner.active:
      detect.delay(partner.id)

@tasks.app.task
def scan(partner_id: str):
  """ Search for new files for a partner and set them up for processing. """
  # get the "copy" sources
  # instantiate the appropriate class
  base_dir = pathlib.Path(__file__).parent.parent.parent.parent / 'rivolifiles'
  cfg = {'path': str(base_dir / 'input')}

  dest_dir = base_dir / 'processed'

  partner = admin_entities.get_partner(partner_id)

  copier = LocalFileCopier(partner, cfg, dest_dir)
  copier.copy()


class Copier(abc.ABC):
  def __init__(self, partner: protos.Partner, cfg: dict[str, str],
               dest_dir: pathlib.Path):
    self.cfg = cfg
    self.dest_dir = dest_dir
    self.partner = partner

  def create_file(self, partner: protos.Partner, orig_file: pathlib.Path,
                  local_file: pathlib.Path, filetype: protos.FileType
                  ) -> int:
    """ Create a file record, rename local file, and schedule loading. """
    # Get a seqential ID. We do this to keep the ID small for the Record rows
    mydb = db.get_db()

    file_id = db.get_next_id('files')

    # Copy the tags from the Partner and the FileType
    tags: dict[str, str] = dict(list(partner.staticTags.items()) +
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
      partnerId=partner.id,
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

    # get # of lines from the file
    line_count = sum(1 for _
        in open(local_file, 'r', encoding='UTF-8').readlines())
    file.stats.approximateRows = line_count

    mydb.files.insert_one(bson_format.from_proto(file))

    new_name = self._file_longterm_name(orig_file, file_id)
    local_file.rename(local_file.with_name(new_name))

    # Schedule loading of the file
    #loader.load.delay(file_id)

    return file_id

  def _parse_date(self, orig_file: pathlib.Path,
      filetype: protos.FileType) -> t.Optional[str]:
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
  def copy(self):
    # Create a log entry
    log = protos.CopyLog(partnerId=self.partner.id, time=bson_format.now())

    # loop through every child in the root directory
    for child in pathlib.Path(self.cfg['path']).iterdir():
      # Currently only support files and not sub directories
      if child.is_file():
        log.files.append(self.evaluate_file(child, self.dest_dir, self.partner))

    db.get_db().copylog.insert_one(bson_format.from_proto(log))


  def evaluate_file(self, file: pathlib.Path,  dest_dir: pathlib.Path,
      partner: protos.Partner) -> protos.CopyLog.EvaluatedFile:
    """ Evaluate a file to determine if it should be copied. """
    filelog = protos.CopyLog.EvaluatedFile(
      name=file.name,
      sizeBytes=file.stat().st_size
    )

    # Has this file already been copied? If so then ignore it.
    testdb = db.get_db()
    files_filter = bson_format.get_filter_map(
        protos.File(partnerId=partner.id, name=file.name),
        ['partnerId', 'name'])
    resp = testdb.files.find_one(files_filter)

    if resp:
      # File has already been copied and we have a File record; update the log
      # and exit.
      filelog.resolution = protos.CopyLog.EvaluatedFile.FILE_EXISTS
      filelog.fileId = resp['_id']
      return filelog

    # A partner can have multiple filetypes, and we're looking for any that are
    # available
    for filetype in partner.fileTypes:
      # A filetype can have multiple match expressions
      for exp in filetype.fileMatches:
        if re.fullmatch(exp, file.name):
          filelog.fileTypeId = filetype.id

          # Move the file to the destination but with a temporary file name
          # The filename will be changed right after the record is created,
          # and this approach makes oprhans obvious
          tmp_file = dest_dir / self._file_temp_name(file.name)
          shutil.copy(file, tmp_file)
          # Create the file record, which also renames the file
          file_id = self.create_file(partner, file, tmp_file, filetype)

          filelog.fileId = file_id
          filelog.resolution = protos.CopyLog.EvaluatedFile.COPIED

          return filelog

    # No matches
    filelog.resolution = protos.CopyLog.EvaluatedFile.NO_MATCH
    return filelog