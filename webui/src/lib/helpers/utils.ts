import { browser } from '$app/environment';
import {
  ProcessingLog,
  ProcessingLog_LogLevel
} from '$lib/rivoli/protos/processing_pb';

export function makeLogMsg(
  message: string,
  level: ProcessingLog_LogLevel = ProcessingLog_LogLevel.INFO
): ProcessingLog {
  return new ProcessingLog({
    level: level,
    time: Math.floor(Date.now() / 1000),
    message: message
  });
}

export function dateTime(timestamp: number | undefined): string {
  return timestamp
    ? new Date(timestamp * 1000).toLocaleString([], {
        dateStyle: 'short',
        timeStyle: 'short'
      })
    : '';
}

export function makeObjectId() {
  function _hex(value: number) {
    return Math.floor(value).toString(16);
  }

  return (
    _hex(Date.now() / 1000) +
    ' '.repeat(16).replace(/./g, () => _hex(Math.random() * 16))
  );
}

export function fmtNum(num: number | BigInt | undefined) {
  return num ? num.toLocaleString() : 0;
}

const escape = browser ? document.createElement('textarea') : null;

export function escapeHTML(html: string): string {
  // Can only be run client-side
  escape.textContent = html;
  return escape.innerHTML;
}

export function syntaxHighlight(json: any) {
  if (typeof json != 'string') {
    json = JSON.stringify(json, undefined, 2);
  }
  json = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    function (match) {
      var cls = 'number';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'key';
        } else {
          cls = 'string';
        }
      } else if (/true|false/.test(match)) {
        cls = 'boolean';
      } else if (/null/.test(match)) {
        cls = 'null';
      }
      return '<span class="' + cls + '">' + match + '</span>';
    }
  );
}
