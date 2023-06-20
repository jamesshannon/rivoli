import { dateTime, escapeHTML, syntaxHighlight } from '$lib/helpers/utils';

// Constant which allows us to determine the row number from the record id
const recordIdMask = (1n << 32n) - 1n;

interface StringMap {
  [key: string]: any;
}

function renderRowNum(data: StringMap, type: string, row: StringMap) {
  // Render a 1-based row number value. The row number can be calculated from
  // the file ID and the record ID.
  let num = BigInt(row.id) & recordIdMask;

  if (type === 'display') {
    return `<div title="${row.id}">${num}</div>`;
  }

  return num;
}

function renderErrors(data: StringMap, type: string, row: StringMap) {
  if (type === 'display' || type === 'filter') {
    // Only show recent errors in the table column
    if (row.recentErrors?.length) {
      return renderLogList(row.recentErrors);
    }
  }

  return '';
}

function renderColumn(
  data: StringMap,
  type: string,
  row: StringMap,
  meta: StringMap
): string {
  // The column will be the same as the field name
  const settings = meta.settings.aoColumns[meta.col];
  const fieldMapKey = settings.rFieldMapKey;
  const colName = settings.sTitle;

  //console.log(fieldMap, colName, settings);
  // If the record has not been (successfully) parsed or validated then the
  // string mapping will be undefined
  if (row[fieldMapKey]) {
    return row[fieldMapKey][colName] || '';
  }

  return '';


  return (row.parsedFields || {})[colName] || '';
}

const configDefault: StringMap = {
  paging: true,
  pageLength: 10,
  searching: true,
  //searchDelay: 400,
  search: {
    return: true,
  },
  dom: 'rft<"controls"ilp>', // hide the search box
  ordering: false,
  serverSide: true,
  deferRender: true,
  scrollX: true
};

export const fileDetailLeftColumns = [
  {
    className: 'table-expandrow',
    orderable: false,
    data: null,
    defaultContent: '<div class="expand-button"></div>'
  },
  {
    title: 'Row',
    data: null,
    render: renderRowNum,
  },
  {
    title: 'Record Type',
    data: 'recordType'
  },
  {
    title: 'Status',
    name: 'status',
    data: 'status'
  }
];

export const errorsColumn = [
  {
    title: 'Recent Errors',
    className: 'errors',
    data: null,
    render: renderErrors
  }
];

// These are values for the ProcessingLog.errorCode enum value. Ideally we'd
// use that generated enum, but in this case the value might be an HTTP status
// code (e.g., 502) which is not a defined enum value (though are reserved).
const processingLogErrorCodes = new Map([
  [600, 'Validation Error'],
  [700, 'Operation Error'],
  [800, 'Execution Error'],
  [801, 'Connection Error'],
  [802, 'Timeout Error']
]);

export function makeDynamicColumns(
  columnNames: Array<string>,
  fieldMapKey: string
): Array<object> {
  // Create a list of table columns from an array of field names. This is
  // used for creating columns for parsed / validated fields.
  return columnNames.map((col) => ({
      title: col,
      data: null,
      className: `record_field ${fieldMapKey}`,
      // Field columns are not visible by default
      visible: false,
      render: renderColumn,
      rFieldMapKey: fieldMapKey,
    }));
}

export function makeDynamicColumnsXXX(
  columnNames: Array<string>,
  includeRowNum: boolean = true,
  includeErrors: boolean = true,
  includeDoneCheckbox: boolean = true,
): Array<object> {
  const cols = [];
  if (includeRowNum) {
    cols.push({
      title: 'Row',
      data: null,
      render: renderRowNum
    });
  }

  cols.push(
    ...columnNames.map((col) => ({
      title: col,
      data: null,
      className: 'record_field',
      render: renderColumn
    }))
  );

  if (includeErrors) {
    cols.push({
      title: 'Errors',
      data: null,
      render: renderErrors
    });
  }

  if (includeDoneCheckbox) {
    cols.push({
      title: 'Done',
      data: null,
      defaultContent: '<input type="checkbox" />'
    });
  }

  return cols;
}

export function getTableConfig(retrieveCallback: any, columns: Array<object>) {
  return { ...configDefault, ...{ ajax: retrieveCallback, columns } };
}

function renderLogList(logs: Array<any>) {
  let html = '<ul>';
  for (let log of logs) {
    html += `<li>
      <h6>${escapeHTML(log.message)}</h6>
      <span>${dateTime(log.time)}</span> -
      ${processingLogErrorCodes.get(log.errorCode) || log.errorCode || ''}
    </li>`;
  }
  return html + '</ul>';
}

export function makeExpandedRow(data: any): string {
  const lines = [];
  if (data.rawColumns) {
    lines.push(`Record #: ${data.id}`);

    lines.push(
      '<div><h5>Raw Columns</h5><pre>' +
        data.rawColumns
          .map((str: string) => `<span class="raw">${str}</span>`)
          .join(',') +
        '</pre></div>'
    );
  }
  if (data.parsedFields) {
    lines.push(
      '<div><h5>Parsed Fields</h5><pre class="pretty_json">' +
        syntaxHighlight(data.parsedFields) +
        '</pre></div>'
    );
  }
  if (data.validatedFields) {
    lines.push(
      '<div><h5>Validated Fields</h5><pre class="pretty_json">' +
        syntaxHighlight(data.validatedFields) +
        '</pre></div>'
    );
  }
  if (data.log?.length) {
    lines.push('<div><h5>Log</h5>' + renderLogList(data.log) + '</div>');
  }

  return '<div class="expanded_row">' + lines.join('') + '</div>';
}
