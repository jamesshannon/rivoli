<script lang="ts">
	import { DataTable } from 'carbon-components-svelte';

	import { ProcessingLog, ProcessingLog_LogSource } from '$lib/protos/processing_pb';

	import { dateTime, makeObjectId } from '$lib/helpers/utils';

	export let logs: Array<ProcessingLog>;

	let headers = [
		{ key: 'time', value: 'Date' },
		{ key: 'source', value: 'Source' },
		{ key: 'message', value: 'Message' }
	];

	// Sometimes (like development) pl.time is not unique and so we need to use
	// a random unique ID
	let rows = logs.reverse().map((pl) => {
		return {
			id: makeObjectId(),
			time: pl.time,
			source: pl.source,
			message: pl.message,
			level: pl.level
		};
	});
</script>

<DataTable size="short" pageSize={10} bind:headers bind:rows>
	<svelte:fragment slot="cell" let:row let:cell>
		{#if cell.key === 'time'}
			{dateTime(cell.value)}
		{:else if cell.key === 'source'}
			{ProcessingLog_LogSource[cell.value]}
		{:else}
			{cell.value}
		{/if}
	</svelte:fragment>
</DataTable>
