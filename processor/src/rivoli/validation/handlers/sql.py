""" Validation handler which runs SQL queries in in-memory SQLite3 database. """
import sqlite3

from rivoli import protos
from rivoli.function_helpers import helpers

# Module-level db connection. Short of re-creating the database on every
# validation, there's no per-execution concept of state. We'd have to
# implement that (maybe as ValidationHandler() classes)? Or maybe create a
# connection cache keyed by (fileid, recordtypeid) and close connections if
# they haven't been used recently.
CONNECTION = sqlite3.connect(':memory:')
CONNECTION.row_factory = sqlite3.Row
CURSOR = CONNECTION.cursor()

# Neither of these methods any sort of inspection or configuration of
# additional parameters that could be used. One option is adding additional --
# possibly named -- bindings when executing the validation SQL, but doesn't
# scale well. Another option is to create a `config` table and populate it
# with instance config, which could then be accessed by a subquery.

def field_validation(cfg: protos.FunctionConfig,
    validator: protos.Function, value: str) -> str:
  """ Validate a specific field using a SQL statement.
  The input value is passed as a parameter and can be accessed with `?`. The
  statement should return either the column `value` or the column
  `_ERROR`. If the `_ERROR` column exists and is non-empty then the value will
  be raised as a ValidationError. If the `value` column exists then its value
  will be returned. If `_ERROR` is empty and value column doesn't exist, or
  no rows are returned, then the original value is returned.
  """
  try:
    result = CURSOR.execute(validator.sqlCode, (value, )).fetchone()
  except sqlite3.DatabaseError as exc:
    raise helpers.ExecutionError(f'SQL Statement Error: {exc.args[0]}')


  if result and '_ERROR' in result.keys() and result['_ERROR']:
    raise helpers.ValidationError(result['_ERROR'])

  # If an error wasn't returned but value was returned then use that
  if result and 'value' in result.keys():
    return result['value']

  # If an error wasn't returned and value wasn't returned then return the
  # input value. This allows the SQL expression to only return an error, and
  # possibly no rows to signify no error.
  return value

def record_validation(cfg: protos.FunctionConfig,
    validator: protos.Function, record: dict[str, str]) -> dict[str, str]:
  """ Validate an entire record using a SQL statement.
  The input record is inserted into a table named `rows`, with columns for each
  value in the record dictionary. The `rows` table will have a single row with
  the records values. The SQL query should return a result set with columns
  which become the new record dictionary. If the result set includes the column
  `_ERROR` and its value is non-empty then its value will be raised as a
  ValidationError. If no rows are returned then the original dict will be
  returned. Note that this means that, if the statement returns a row, the SQL
  is responsible for returning all rows that should be in the record; a
  pattern like `SELECT *, IF(..., 'x') AS _ERROR FROM rows` might be useful.
  """
  # Create the table with an AS SELECT in the form of ? as col1, ? as col2, ...
  sql = f'CREATE TABLE rows AS SELECT ? {", ? as ".join(record.keys())}'

  try:
    CURSOR.execute(sql, list(record.values()))
    # Run the user SQL
    result = CURSOR.execute(validator.sqlCode).fetchone()

  except sqlite3.DatabaseError as exc:
    raise helpers.ExecutionError(f'SQL Statement Error: {exc.args[0]}')
  finally:
    CURSOR.execute('DROP TABLE rows')

  if not result:
    return record

  if '_ERROR' in result.keys() and result['_ERROR']:
    raise helpers.ValidationError(result['_ERROR'])

  return {key: result[key] for key in result.keys() if not key.startswith('_')}
