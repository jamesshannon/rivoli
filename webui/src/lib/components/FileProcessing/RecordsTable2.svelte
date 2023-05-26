<script lang="ts">

  import { SvelteDataTable } from '@mac-barrett/svelte-data-table';

  interface ColumnGroup {
    key?: string;
    title?: string;
    visible: boolean;
    length: number;
  }

  export let recordsDataTable: SvelteDataTable;
  export let columnGroups: Array<ColumnGroup>;

  export function resizeTable() {
    // The datatable doesn't auto-size correctly if it's instantiated while
    // hidden. Call this to resize.
    document.getElementById('table')!.style.width = '100%';
    recordsDataTable?.getAPI()?.columns.adjust().draw();
  }

</script>
