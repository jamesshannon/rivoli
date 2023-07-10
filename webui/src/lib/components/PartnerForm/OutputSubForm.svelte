<script lang="ts">
  import { getContext } from 'svelte';
  import {
    Accordion,
    AccordionItem,
    Button,
    Checkbox,
    Dropdown,
    Grid,
    Row,
    Column,
    FormGroup,
    FormLabel,
    TextInput,
    MultiSelect
  } from 'carbon-components-svelte';
  import Add from 'carbon-icons-svelte/lib/Add.svelte';

  import { makeObjectId } from '$lib/helpers/utils';
  import type { FileType, Output } from '$lib/rivoli/protos/config_pb';
  import FunctionEditor from './FunctionEditor.svelte';
  import FunctionMultiEditor from './FunctionMultiEditor.svelte';
  import StringList from '$lib/components/StringList.svelte';
  import FieldTypeSubForm from './FieldTypeSubForm.svelte';
  import type { Function } from '$lib/rivoli/protos/functions_pb';import {
    Record,
    Record_RecordTypeRef,
    Record_Status
  } from '$lib/rivoli/protos/processing_pb';

  export let filetype: FileType;
  export let output: Output;

  let functionsMap: Map<string, Function> = getContext('FUNCTIONS');

  const statusItems = [
    { id: Record_Status.VALIDATION_ERROR, text: 'VALIDATION_ERROR' },
    { id: Record_Status.UPLOAD_ERROR, text: 'UPLOAD_ERROR' }
  ];

  // Create an array of all the IDs for the recordTypes' validation functions
  // PLUS the recordTypes' fieldTypes' validation functions PLUS
  // any existing configuration failed function/
  // De-dup using a set()
  $: validationFunctions = [...new Set(filetype.recordTypes.flatMap(
    (rt) => rt.validations.flatMap(
      (v) => v.functionId
    )).concat(filetype.recordTypes.flatMap(
      (rt) => rt.fieldTypes.flatMap(
        (ft) => ft.validations.flatMap(
          (v) => v.functionId))
    )).concat(output.configuration!.failedFunctionConfigs))];

  // Get an array of all functions given the above function IDs.
  $: vf = validationFunctions.map((fId) => functionsMap.get(fId));

  // And then convert it to an Items array for the MultiSelect
  $: failedFunctionItems = validationFunctions.map((fId) => ({
    id: fId,
    text: functionsMap.get(fId)!.name
  }));
</script>

<Grid>
  <Row>
    <Column>
      <TextInput labelText="Output Name" bind:value={output.name} />
    </Column>
    <Column>
      <Checkbox labelText="Active" bind:checked={output.active} />
    </Column>
  </Row>
  <Row>
    <Column>Destination Type: File</Column>
    <Column />
  </Row>

  <FormGroup legendText="File Destination Configuration">
    <Row>
      <Column>
        <TextInput
          labelText="File Path Pattern"
          bind:value={output.file.filePathPattern}
        />
      </Column>
      <Column>
        <Checkbox
          labelText="Run Automatically"
          bind:checked={output.file.runAutomatic}
        />
      </Column>
    </Row>
  </FormGroup>

  <FormGroup legendText="Report Configuration">
    <Row>
      <Column>
        <Checkbox
          labelText="All Record Types"
          bind:checked={output.configuration.allRecordTypes}
        />
        -- or list of recordtypes --
      </Column>
      <Column />
    </Row>
    <Row>
      <Column>
        <MultiSelect
          titleText="Statuses"
          label="Select..."
          sortItem={() => {}}
          items={statusItems}
          bind:selectedIds={output.configuration.recordStatuses}
        />
      </Column>
      <Column>
        <Checkbox
          labelText="Duplicate Input Fields"
          bind:checked={output.configuration.duplicateInputFields}
        />
        <Checkbox
          labelText="Include Recent Errors"
          bind:checked={output.configuration.includeRecentErrors}
        />
      </Column>
    </Row>
    <Row>
      <Column>
      <Column>
        <MultiSelect
          titleText="Failed Functions"
          label="Select..."
          items={failedFunctionItems}
          bind:selectedIds={output.configuration.failedFunctionConfigs}
        />
      </Column>
    </Row>
  </FormGroup>
</Grid>
