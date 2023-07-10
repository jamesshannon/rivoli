<script lang="ts">
  import {
    Checkbox,
    Grid,
    Row,
    Column,
    Form,
    FormGroup,
    FormLabel,
    NumberInput,
    TextArea,
    TextInput
  } from 'carbon-components-svelte';

  import {
    FileType_Format,
    FieldType,
    type FileType,
    FixedWidthFieldRange
  } from '$lib/rivoli/protos/config_pb';

  import FunctionMultiEditor from './FunctionMultiEditor.svelte';
  import { Function_FunctionType } from '$lib/rivoli/protos/functions_pb';

  export let fieldtype: FieldType;
  export let filetype: FileType;

  // Svelte goes into an infinite reactive loop on the filetype fields, so we
  // need to manage our own de-bouncer by comparing to previous values.
  const fieldLocationValues: [FileType_Format | null, boolean | null] = [
    null,
    null
  ];

  $: {
    let format = filetype.format;
    let hasHeader = filetype.hasHeader;

    if (
      format !== fieldLocationValues[0] ||
      hasHeader !== fieldLocationValues[1]
    ) {
      fieldLocationValues[0] = format;
      fieldLocationValues[1] = hasHeader;

      if (format === FileType_Format.FLAT_FILE_DELIMITED && hasHeader
          && fieldtype.fieldLocation.case !== 'headerColumn') {
        fieldtype.fieldLocation = { case: 'headerColumn', value: '' };;
      } else if (format === FileType_Format.FLAT_FILE_DELIMITED && !hasHeader
          && fieldtype.fieldLocation.case !== 'columnIndex') {
        fieldtype.fieldLocation = { case: 'columnIndex', value: 0 };
      } else if (format === FileType_Format.FLAT_FILE_FIXED_WIDTH
          && fieldtype.fieldLocation.case !== 'charRange') {
        fieldtype.fieldLocation = {
          case: 'charRange',
          value: new FixedWidthFieldRange() };
      }
    }
  }
</script>

<FormGroup>
  <Grid>
    <Row>
      <Column>
        <TextInput
          labelText="Field Name"
          helperText="UPPER_CASE format is recommended"
          bind:value={fieldtype.name} />
      </Column>
      <Column>
        <Checkbox labelText="Active" bind:checked={fieldtype.active} />
        <Checkbox
          labelText="Sensitve Field"
          bind:checked={fieldtype.isSensitive}
        />
        <Checkbox labelText="Shared Key" bind:checked={fieldtype.isSharedKey} />
      </Column>
    </Row>
    <Row>
      <Column>
        <TextArea labelText="Description" bind:value={fieldtype.description} />
      </Column>
      <Column>
        {#if fieldtype.fieldLocation.case === 'headerColumn'}
          <!-- Delimited With Header -->
          <TextInput
            labelText="Header Column Name"
            helperText="adfjadf jasf"
            bind:value={fieldtype.fieldLocation.value}
          />
        {:else if fieldtype.fieldLocation.case === 'columnIndex'}
          <!-- Delimited Without Header -->
          <NumberInput hideSteppers label="Header Column Index" min={1} />
        {:else if fieldtype.fieldLocation.case === 'charRange'}
          <!-- Fixed-width -->
          <NumberInput label="Start" min={1} bind:value={fieldtype.fieldLocation.value.start} />
          <NumberInput label="End" min={1} bind:value={fieldtype.fieldLocation.value.end} />
        {/if}
      </Column>
    </Row>
    <Row>
      <Column>
        <FormLabel>Field Validations</FormLabel>
        <FunctionMultiEditor
          bind:functionConfigs={fieldtype.validations}
          functionType={Function_FunctionType.FIELD_VALIDATION}
        />
      </Column>
      <Column />
    </Row>
  </Grid>
</FormGroup>
