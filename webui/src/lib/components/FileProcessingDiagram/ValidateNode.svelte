<script lang="ts">
  import { FunctionMath } from 'carbon-icons-svelte';

  import type { ValidationNode } from '$lib/helpers/processing_graph';
  import { getNodeStatus } from '$lib/helpers/file_processing/diagram';
  import {
    File_Status,
    type File,
    StepStats
  } from '$lib/rivoli/protos/processing_pb';

  import DefaultNode from '$lib/components/FileProcessingDiagram/DefaultNode.svelte';
  import Layout from '$lib/components/FileProcessingDiagram/Layout.svelte';

  export let node: ValidationNode;
  export let file: File | undefined = undefined;

  $: status = getNodeStatus(
    file!,
    File_Status.VALIDATING,
    File_Status.VALIDATE_ERROR,
    File_Status.VALIDATED
  );

  let key: string;
  if (file) {
    let keyItems = ['VALIDATE', node.record.id];
    if (node.field) {
      keyItems.push(node.field.id);
    }
    keyItems.push(node.cfg.id);
    key = keyItems.join(':');
  }

  $: stepStat = key ? file?.stats?.steps[key] : undefined;
  $: inputCount = (stepStat?.input || '').toString();
</script>

<DefaultNode {node} {status} {inputCount} width={450}>
  <Layout
    icon={FunctionMath}
    titleText={node.name}
    description="Validate Field"
  >
    {#if stepStat}
      {stepStat.success} successes<br />
      {stepStat.failure} failures<br />
    {/if}
  </Layout>
</DefaultNode>
