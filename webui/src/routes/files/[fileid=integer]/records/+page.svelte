<script lang="ts">
  import "carbon-components-svelte/css/g10.css";

  import {
    Breadcrumb, BreadcrumbItem,
  } from "carbon-components-svelte";

  import { onMount } from 'svelte';

  import type { PageData } from './$types';

  import FileStatus from "$lib/components/FileStatus.svelte";

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table'


  import {dateTime} from "$lib/helpers/utils";
	import type { Partner, FileType } from "$lib/protos/config_pb";
	import { File_Status, Record_RecordTypeRef, type File } from "$lib/protos/processing_pb";

  import SubtractAlt from "carbon-icons-svelte/lib/SubtractAlt.svelte";


  export let data: PageData;
  let file = data.file;
  const filetype = data.filetype;



  async function retrieveRecords(data, callback, settings) {
    const records = [];
    const recordIdMask = (1n << 32n) - 1n;

    const result = await client.retrieveRecords({fileId: file.id});

    for (let record of result.records) {
      // do some conversion
      let doc = record.toJson();

      doc.id = BigInt(doc.id) & recordIdMask;
      if (typeof doc.recordType === 'number') {
        doc.recordType = 'lookup';
      }

      records.push(doc);
    }
    console.log(records[3]);
    callback({data: records});
  }

  function renderErrors(data, type: string, row) {
    if (type === 'display' || type === 'filter') {
      if (row['validationErrors']?.length) {
        return row['validationErrors'].map((ve) => `${ve.field || '[row]'}: ${ve.error}`).join('<br />')
      }
    }

    return '';
  }

  // What to show?
  // NEW - Not much
  // LOADED - recordType, status, errors, rawColumns (or rawLine)
  // PARSED - parsedFields dict
  // VALIDATED - validatedFields dict (this is the final dict, but
  //   it's per record type, and might have even been changed by the  validators
  //   maybe loop through the first 100 (?) records (by record id) and build the
  //   column list?
  //

  function makeExpandedRow(data): string {
    const lines = [];
    if (data.rawColumns) {
      lines.push('<div><h5>Raw Columns</h5>' +
          data.rawColumns.map((str: string) => `<span>${str}</span>`)
          .join(',') + '</div>');
    }
    if (data.parsedFields) {
      lines.push('<div><h5>Parsed Fields</h5>' +
          JSON.stringify(data.parsedFields, null, 2) + '</div>');
    }
    if (data.validatedFields) {
      lines.push('<div><h5>Validated Fields</h5>' +
          JSON.stringify(data.validatedFields, null, 2) + '</div>');
    }

    return '<div class="expanded_row">' + lines.join('') + '</div>';
  }

  function expandRowHandler(evt: MouseEvent) {
    if ((evt.target as HTMLElement).classList.contains('expand-button')) {
      let tr = (evt.target as HTMLElement).parentElement!.parentElement!;
      let row = myDataTable.getAPI()?.row(tr)!;

      if (row.child.isShown()) {
        row.child.hide();
        tr.classList.remove('expanded')
      } else {
        tr.classList.add('expanded')
        row.child(makeExpandedRow(row.data())).show();
      }
    }
  }

  let config = {
      paging: true,
      searching: true,
      ordering: false,
      //serverSide: true, https://datatables.net/reference/option/serverSide
      deferRender: true,
      ajax: retrieveRecords,
      columns: [
        {
          className: 'table-expandrow',
          orderable: false,
          data: null,
          defaultContent: '<div class="expand-button"></div>',

        },
        {
          title: 'Record',
          data: 'id',
        },
        {
          title: 'Record Type',
          data: 'recordType',
        },
        {
          title: 'Status',
          data: 'status'
        },
        {
          title: 'Errors',
          data: null,
          render: renderErrors,
        }
      ]
  };

let myDataTable: SvelteDataTable;

onMount(async () => {
	console.log(myDataTable.getAPI());
})

</script>


<Breadcrumb noTrailingSlash>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/files">File Processing</BreadcrumbItem>
  <BreadcrumbItem href="/files/{ file.id }">{ file.name }</BreadcrumbItem>
  <BreadcrumbItem href="/files/{ file.id }/records" isCurrentPage>Records</BreadcrumbItem>
</Breadcrumb>

<div class="local" on:click={expandRowHandler}>
  <SvelteDataTable bind:this={myDataTable} config={config} />
</div>

<style>

.local :global(div.expand-button) {
  cursor: pointer;
  position: relative;
  width: 15px;
  height: 15px;
}

.local :global(div.expand-button:before),
.local :global(div.expand-button:after) {
  content: "";
  position: absolute;
  background-color: darkgray;
  transition: transform 0.25s ease-out;
}

/* vertical line */
.local :global(div.expand-button:before) {
  top: 0;
  left: 50%;
  width: 4px;
  height: 100%;
  margin-left: -2px;
}

/* horizontal line */
.local :global(div.expand-button::after) {
  top: 50%;
  left: 0;
  width: 100%;
  height: 4px;
  margin-top: -2px;
}

.local :global(div.expand-button:hover:before),
.local :global(div.expand-button:hover:after) {
  background-color: rgb(126, 135, 169);
}

.local :global(tr.expanded div.expand-button:before) {
  transform: rotate(90deg);
}

.local :global(tr.expanded div.expand-button:after) {
  transform: rotate(180deg);
}

.local :global(div.expanded_row) {
  font-family: Consolas, "Andale Mono WT", "Andale Mono", "Lucida Console", "Lucida Sans Typewriter", "DejaVu Sans Mono", "Bitstream Vera Sans Mono", "Liberation Mono", "Nimbus Mono L", Monaco, "Courier New", Courier, monospace;
  white-space: pre-wrap;
}

.local :global(div.expanded_row span) {
  background: #DDDDDD;
}

</style>
