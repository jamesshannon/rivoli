<script lang="ts">
  import {
    Accordion,
    AccordionItem,
    Button,
    Checkbox,
    Dropdown,
    Grid,
    NumberInput,
    Row,
    Column,
    Form,
    FormGroup,
    FormLabel,
    Tabs,
    Tab,
    TabContent,
    TextInput
  } from 'carbon-components-svelte';
  import Add from 'carbon-icons-svelte/lib/Add.svelte';

  import { makeObjectId } from '$lib/helpers/utils';
  import { FieldType, FileType, RecordType } from '$lib/protos/config_pb';
  import FunctionEditor from './FunctionEditor.svelte';
  import FunctionMultiEditor from './FunctionMultiEditor.svelte';
  import StringList from '$lib/components/StringList.svelte';
  import FieldTypeSubForm from './FieldTypeSubForm.svelte';
  import { Function_FunctionType } from '$lib/protos/functions_pb';

  export let recordtype: RecordType;
  export let filetype: FileType;

  function addNewFieldType() {
    recordtype.fieldTypes.push(
      new FieldType({ id: makeObjectId(), active: true })
    );
    recordtype.fieldTypes = recordtype.fieldTypes;
  }
</script>

<Grid>
  <Row>
    <Column
      ><TextInput
        labelText="Record Type Name"
        bind:value={recordtype.name}
      /></Column
    >
  </Row>
  <Row>
    <Column>
      <FormLabel>Record Matches</FormLabel>
      <StringList bind:strings={recordtype.recordMatches} />
    </Column>
    <Column />
  </Row>

  <FormGroup legendText="Processing Functions">
    <Row>
      <Column>
        <FormLabel>Record Validations</FormLabel>
        <FunctionMultiEditor
          bind:functionConfigs={recordtype.validations}
          functionType={Function_FunctionType.RECORD_VALIDATION}
        />
      </Column>
      <Column />
    </Row>
    <Row>
      <Column>
        <FunctionEditor
          labelText="Upload Function"
          bind:functionConfig={recordtype.upload}
          functionType={[
            Function_FunctionType.RECORD_UPLOAD,
            Function_FunctionType.RECORD_UPLOAD_BATCH
          ]}
        />
      </Column>
      <Column />
    </Row>
  </FormGroup>

  <h3>Fields</h3>
  <Button
    kind="secondary"
    iconDescription="Add New Field Type"
    icon={Add}
    on:click={addNewFieldType}
  />
  <Accordion align="start">
    {#each recordtype.fieldTypes as fieldtype}
      <AccordionItem open={false}>
        <svelte:fragment slot="title">
          <h3>{fieldtype.name || '[New Field]'}</h3>
          <code>{fieldtype.fieldLocation.value} -&gt; {fieldtype.name}</code>
          <!-- Need to format this richly, including active status-->
        </svelte:fragment>
        <FieldTypeSubForm bind:fieldtype {filetype} />
      </AccordionItem>
    {/each}
  </Accordion>
</Grid>
