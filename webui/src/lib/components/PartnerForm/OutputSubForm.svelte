<script lang="ts">
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
  import type { Output } from '$lib/rivoli/protos/config_pb';
  import FunctionEditor from './FunctionEditor.svelte';
  import FunctionMultiEditor from './FunctionMultiEditor.svelte';
  import StringList from '$lib/components/StringList.svelte';
  import FieldTypeSubForm from './FieldTypeSubForm.svelte';
  import { Function_FunctionType } from '$lib/rivoli/protos/functions_pb';
  import {
    Record,
    Record_RecordTypeRef,
    Record_Status
  } from '$lib/rivoli/protos/processing_pb';

  export let output: Output;

  const statusItems = [
    { id: Record_Status.VALIDATION_ERROR, text: 'VALIDATION_ERROR' },
    { id: Record_Status.UPLOAD_ERROR, text: 'UPLOAD_ERROR' }
  ];
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
        <!-- <FunctionEditor
          labelText="Upload Function"
          bind:functionConfig={recordtype.upload}
          functionType={[
            Function_FunctionType.RECORD_UPLOAD,
            Function_FunctionType.RECORD_UPLOAD_BATCH
          ]}
        /> -->
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
        Failed Functions:
        {output.configuration.failedFunctionConfigs}
      </Column>
    </Row>
  </FormGroup>
</Grid>
