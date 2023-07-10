<script lang="ts">
  import { CloudUpload } from 'carbon-icons-svelte';

  import { getNodeStatus } from '$lib/helpers/file_processing/diagram';
  import type { Node as NodeClass } from '$lib/helpers/processing_graph';
  import { File_Status, type File } from '$lib/rivoli/protos/processing_pb';

  import DefaultNode from '$lib/components/FileProcessingDiagram/DefaultNode.svelte';
  import Layout from '$lib/components/FileProcessingDiagram/Layout.svelte';

  export let node: NodeClass;
  export let file: File | undefined = undefined;

  $: status = getNodeStatus(
    file,
    File_Status.LOADING,
    File_Status.LOAD_ERROR,
    File_Status.LOADED
  );

  $: inputCount = file?.stats?.steps['LOAD']?.input || '';
</script>

<DefaultNode {node} {status} {inputCount}>
  <Layout icon={CloudUpload} titleText={node.name} description="Load Records">
    {#if file}
      {file.stats?.loadedRecordsSuccess} records
    {/if}
  </Layout>
</DefaultNode>
