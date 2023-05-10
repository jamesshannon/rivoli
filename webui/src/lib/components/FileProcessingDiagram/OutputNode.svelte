<script lang="ts">
  import { Report } from 'carbon-icons-svelte';

  import { getNodeStatus } from '$lib/helpers/file_processing/diagram';
  import type { Node as NodeClass } from '$lib/helpers/processing_graph';
  import { File_Status, type File } from '$lib/rivoli/protos/processing_pb';

  import DefaultNode from '$lib/components/FileProcessingDiagram/DefaultNode.svelte';
  import Layout from '$lib/components/FileProcessingDiagram/Layout.svelte';

  export let node: NodeClass;
  export let file: File | undefined = undefined;

  if (file) {
    // node.id is not the report id
    const inst = file.outputs.reverse().find((o) => o.outputId === node.id);
    if (inst) {
      // inst is the most-recent report instance. we ignore previous ones.
    }
  }

  $: status = getNodeStatus(
    file!,
    File_Status.PARSING,
    File_Status.PARSE_ERROR,
    File_Status.PARSED
  );

  $: inputCount = file?.stats?.steps['PARSE']?.input.toString() || '';
</script>

<DefaultNode {node} showOutputAnchors={false}>
  <Layout icon={Report} titleText={node.name} description="Parse Fields">
    {#if file}
      {file.stats?.loadedRecordsSuccess} rows
    {/if}
  </Layout>
</DefaultNode>
