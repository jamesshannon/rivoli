<script lang="ts">
	import { Breadcrumb, BreadcrumbItem, Button } from 'carbon-components-svelte';

	import Add from 'carbon-icons-svelte/lib/Add.svelte';

	import { onMount } from 'svelte';

	import { SvelteDataTable } from '@mac-barrett/svelte-data-table';
	import type { PageData } from './$types';

	import { File_Status } from '$lib/protos/processing_pb';

	export let data: PageData;
	const partnerMap = data.partnerMap;
	const filetypeMap = data.filetypeMap;

	function renderFileName(data, type: String, row) {
		if (type === 'display') {
			return `<a href="/files/${row['id']}">${row['name']}</a>`;
		}

		return data;
	}

	function renderDate(data, type: string, row) {
		if (type === 'display') {
			return new Date(row['created'] * 1000).toLocaleString([], {
				dateStyle: 'short',
				timeStyle: 'short'
			});
		}

		return data;
	}

	function renderRecordCount(data, type: String, row) {
		if (type === 'display') {
			return row.stats?.totalRows ? row.stats.totalRows : `~ ${row.stats.approximateRows}`;
		}

		return data;
	}

	function renderPartnerName(data, type: string, row) {
		return `<a href="/partners/${row.partnerId}">${partnerMap.get(row.partnerId).name}</a>`;
	}

	function renderFileTypeName(data, type: string, row) {
		return `<a href="/partners/${row.partnerId}/filetypes/${row.fileTypeId}">${
			filetypeMap.get(row.fileTypeId).name
		}</a>`;
	}

	function renderStatus(data, type: string, row) {
		return File_Status[row.status] || '';
	}

	let config = {
		paging: true,
		searching: true,
		ordering: false,
		//serverSide: true,
		deferRender: true,
		ajax: async (tableData, callback, settings) => {
			// get from server
			console.log(tableData);

			callback({ data: data.files, recordsTotal: 1000 });
		},
		columns: [
			{
				title: 'File',
				data: 'id',
				render: renderFileName
			},
			{
				title: 'Partner',
				data: 'partnerId',
				render: renderPartnerName
			},
			{
				title: 'File Type',
				data: 'fileTypeId',
				render: renderFileTypeName
			},
			{
				title: 'Date',
				data: 'created',
				render: renderDate
			},
			{
				title: 'Row Count',
				data: 'status',
				render: renderRecordCount
			},
			{
				title: 'Status',
				data: 'status',
				render: renderStatus,
			}
		]
	};

	/**
	 * @type {SvelteDataTable}
	 */
	let myDataTable;
	// let headers = ['One', 'Two', 'Three', 'Four'];
	// let rows = [['1', '2', '3', '5']];

	// onMount(async () => {
	// 	console.log(myDataTable.getAPI());
	// })

	// export const customDirective = (node) => {
	//   onMount(() => {
	//       // other logic
	//       console.log(myDataTable.getAPI());
	//   });
	//}

	//let rows = data.partners.map((p) => ({'id': p.id, 'name': p.name}));
	//console.log(rows);
</script>

<Breadcrumb noTrailingSlash>
	<BreadcrumbItem href="/">Home</BreadcrumbItem>
	<BreadcrumbItem href="/partners" isCurrentPage>File Processing</BreadcrumbItem>
</Breadcrumb>

<SvelteDataTable bind:this={myDataTable} {config} />
