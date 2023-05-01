<script lang="ts">
  import {
    Button,
    Checkbox,
    Dropdown,
    Grid,
    Row,
    Column,
    Form,
    FormGroup,
    FormLabel,
    NumberInput,
    Tabs,
    Tab,
    TabContent,
    TextArea,
    TextInput
  } from 'carbon-components-svelte';

  import {
    FileType_Format,
    FieldType,
    type FileType
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

      if (format === FileType_Format.FLAT_FILE_DELIMITED && hasHeader) {
        fieldtype.fieldLocation.case = 'headerColumn';
      } else if (format === FileType_Format.FLAT_FILE_DELIMITED && !hasHeader) {
        fieldtype.fieldLocation.case = 'columnIndex';
      }
    }
  }
</script>

<FormGroup>
  <Grid>
    <Row>
      <Column>
        <TextInput labelText="Field Name" bind:value={fieldtype.name} />
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
          <TextInput
            labelText="Header Column Name"
            helperText="adfjadf jasf"
            bind:value={fieldtype.fieldLocation.value}
          />
        {:else}
          # Delimited Without Header
          <NumberInput hideSteppers label="Header Column Index" min="1" />
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
