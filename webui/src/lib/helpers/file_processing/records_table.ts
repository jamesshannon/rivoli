import { dateTime, escapeHTML, syntaxHighlight } from '$lib/helpers/utils';

function renderRowNum(data, type: string, row) {
  if (type === 'display') {
    return `<div title="${row.id}">${row.num}</div>`;
  }

  return row.num;
}

function renderErrors(data, type: string, row) {
  if (type === 'display' || type === 'filter') {
    // Only show recent errors in the table column
    if (row.recentErrors?.length) {
      return renderLogList(row.recentErrors);
    }
  }

  return '';
}

const configDefault = {
  paging: true,
  pageLength: 10,
  searching: true,
  dom: 'lrtip', // hide the search box
  ordering: false,
  serverSide: true,
  deferRender: true,

  columns: [
    {
      className: 'table-expandrow',
      orderable: false,
      data: null,
      defaultContent: '<div class="expand-button"></div>'
    },
    {
      title: 'Row',
      data: null,
      render: renderRowNum
    },
    {
      title: 'Record Type',
      data: 'recordType'
    },
    {
      title: 'Status',
      name: 'status',
      data: 'status'
    },
    {
      title: 'Recent Errors',
      data: null,
      render: renderErrors
    }
  ]
};

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

export function getTableConfig(retrieveCallback: any) {
  return { ...configDefault, ...{ ajax: retrieveCallback } };
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
