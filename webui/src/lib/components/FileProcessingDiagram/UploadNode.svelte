<script lang="ts">
  import { FunctionMath } from 'carbon-icons-svelte';

  import type { RecordUploadNode } from '$lib/helpers/processing_graph';
  import { getNodeStatus } from '$lib/helpers/file_processing/diagram';
  import { File_Status, type File } from '$lib/rivoli/protos/processing_pb';

  import DefaultNode from '$lib/components/FileProcessingDiagram/DefaultNode.svelte';
  import Layout from '$lib/components/FileProcessingDiagram/Layout.svelte';

  export let node: RecordUploadNode;
  export let file: File | undefined = undefined;

  $: status = getNodeStatus(
    file!,
    File_Status.UPLOADING,
    File_Status.UPLOAD_ERROR,
    File_Status.UPLOADED
  );

  let key = file ? ['UPLOAD', node.record.id, node.cfg.id].join('.') : '';

  $: stepStat = key ? file?.stats?.steps[key] : undefined;
  $: inputCount = (stepStat?.input || 0).toString();
</script>

<DefaultNode {node} {status} {inputCount} width={450}>
  <Layout icon={FunctionMath} titleText={node.name} description="Upload Record">
    {#if file}
      Uploaded {file.stats?.uploadedRecordsSuccess} rows
    {/if}
  </Layout>
</DefaultNode>
