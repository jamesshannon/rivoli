""" Reporter """
import abc
import csv
import datetime
import io
import pathlib
import typing as t

from rivoli import admin_entities
from rivoli import config
from rivoli import db
from rivoli import protos
from rivoli import record_processor
from rivoli.function_helpers import helpers
from rivoli.utils import tasks

# File Formatting
# Python strftime strings for ... current time?, plus
# original filename base

FieldValueGenerator = t.Callable[[protos.Record], list[str]]
""" FieldValueGenerators take in the Record and return the field value(s).
These can return one or more values depending on what's being generated. E.g.,
"loaded columns" will return a string for each original column.
"""

@tasks.app.task
def report(file_id: int, report_id: str) -> None:
  file = db.get_one_by_id('files', file_id, protos.File)

  partner = admin_entities.get_partner(file.partnerId)
  filetype = admin_entities.get_filetype(file.fileTypeId)

  # get report
  config = {
    'name': 'Exception Report',
    'type': 'CSV',
    'header': True,
    'record_status_all': True,
    'record_status_gte': protos.Record.VALIDATION_ERROR,
    'record_statuses': [protos.Record.VALIDATION_ERROR, protos.Record.UPLOAD_ERROR],
    'record_type': 1000,

    'duplicate_input_fields': True,
    'fields': [''], # need to differentiate between different steps
    'include_recent_errors': True,
  }

  file_report_config = {
    'config': config,
    'file_path_pattern': '/reports/zip/d2c/{ORIG_FILE_STEM}-{NOW_TS}-EXCEPTIONS.CSV',
  }

  reporter = CsvReporter(file, partner, filetype, file_report_config)
  reporter.process()


def _fval_recent_errors(record: protos.Record) -> list[str]:
  """ Return text of recent errors. """
  return [', '.join([e.message for e in record.recentErrors])]

def _fvals_original_columns(record: protos.Record) -> list[str]:
  """ Return the original loaded values. """
  return list(record.rawColumns)

# TODO
# * Save file status at end, add log entry

class Reporter(record_processor.DbChunkProcessor):
  """ Base class to create processing reports. """
  log_source = protos.ProcessingLog.UPLOADER # FIXME

  _success_status = protos.File.REPORTED
  _success_status = protos.File.REPORT_ERROR

  _only_process_record_status = False

  def __init__(self, file: protos.File, partner: protos.Partner,
      filetype: protos.FileType, report_config: dict[str, t.Any]) -> None:
    super().__init__(file, partner, filetype)

    self.report_config = report_config

    # Length of field names should be the length of the output list post-
    # generation (which might be different than the length of generators).
    self._field_names: list[str] = []
    """ List of field names, used to create the header. """
    self._field_generators: list[FieldValueGenerator] = []
    """ List of field generators """

    # Keep default db chunk size, don't batch processing
    # No chunk pre-processing necessary
    # We don't want to write back to the File, and definitely not the Records

    root = pathlib.Path(config.get('FILES'))
    self._report_path = self._make_file_path(
        root, report_config['file_path_pattern'])

  def _make_file_path(self, root: pathlib.Path, template: str) -> pathlib.Path:
    """ Return a report file path made from a formatted template. """
    now = datetime.datetime.now()
    filename_vars: dict[str, str] = {
      'NOW_TS': str(int(now.timestamp())),
      'ORIG_FILE_STEM': pathlib.Path(self.file.name).stem
    }

    # Files should always be relative to the root path, and a leading / will
    # essentially ignore the root
    relative_path = template.format(**filename_vars).lstrip('/')
    report_path = root / relative_path
    report_path.parent.mkdir(parents=True, exist_ok=True)

    return report_path

  @abc.abstractmethod
  def _writer_open(self, header: t.Optional[list[str]]):
    """ Open the writer """

  @abc.abstractmethod
  def _write_line(self, values: list[str]):
    """ Write a line """

  @abc.abstractmethod
  def _writer_close(self):
    """ Close the writer """

  def _process(self):
    """ Create report based on instance config. """
    # Check for invariants
    if self.report_config['config']['header'] and not self.file.headerColumns:
      raise ValueError('invalid')

    # Create fields headers and value generators
    if self.report_config['config']['duplicate_input_fields']:
      # Copy all of the original input fields. These are in the rawColumns field
      # in the Record
      self._field_names.extend(list(self.file.headerColumns))
      self._field_generators.append(_fvals_original_columns)

    if self.report_config['config']['include_recent_errors']:
      # Add a column with any errors
      self._field_names.append('Errors')
      self._field_generators.append(_fval_recent_errors)

    self._writer_open(self._field_names)

    # build the filter
    filter_ = {}
    if False and self.report_config['config']['record_status_all']:
      pass
    elif False and self.report_config['config']['record_status_gte']:
      pass
    elif self.report_config['config']['record_statuses']:
      filter_['status'] = {'$in': self.report_config['config']['record_statuses']}

    print(filter_)

    self._process_records(self._get_some_records(filter_))

    # Done. Add a log entry.

    msg = f'Generated {self.report_config["config"]["name"]} and saved to CSV'
    self.file.log.append(self._make_log_entry(False, msg))
    # Can't update status because there might be others, so let
    # status_scheduler figure that out.
    self._update_file(['log'])



  def _process_record(self, records: list[helpers.Record]) -> None:
    """ Write a single record to the report. """
    assert len(records) == 1

    record = records[0].orig_record
    field_values: list[str] = []

    for field_func in self._field_generators:
      field_values.extend(field_func(record))

    self._write_line(field_values)

  def _close_processing(self) -> None:
    # Do nothing
    pass

class CsvReporter(Reporter):
  """ CSV Report Writer, includes header and no header. """
  _file: io.TextIOWrapper
  _writer: t.Any

  def _writer_open(self, header: t.Optional[list[str]]):
    self._file = self._report_path.open('w')
    self._writer = csv.writer(self._file)

    if header:
      self._writer.writerow(header)

  def _write_line(self, values: list[str]):
    self._writer.writerow(values)

  def _writer_close(self):
    self._file.close()
