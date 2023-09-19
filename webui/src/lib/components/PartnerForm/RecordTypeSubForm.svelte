<script lang="ts">
  import { getContext } from 'svelte';

  import {
    Button,
    DataTable,
    Grid,
    Row,
    Column,
    FormGroup,
    FormLabel,
    TextInput
  } from 'carbon-components-svelte';
  import Add from 'carbon-icons-svelte/lib/Add.svelte';

  import { makeObjectId } from '$lib/helpers/utils';
  import {
    FieldType,
    FileType,
    FileType_Format,
    FixedWidthFieldRange,
    FunctionConfig,
    RecordType
  } from '$lib/rivoli/protos/config_pb';
  import FunctionEditor from './FunctionEditor.svelte';
  import FunctionMultiEditor from './FunctionMultiEditor.svelte';
  import StringList from '$lib/components/StringList.svelte';
  import FieldTypeSubForm from './FieldTypeSubForm.svelte';
  import { type Function, Function_FunctionType } from '$lib/rivoli/protos/functions_pb';

  export let recordtype: RecordType;
  export let filetype: FileType;

  let functionsMap: Map<string, Function> = getContext('FUNCTIONS');

  let locationHeader = '';
  let locationValueFn: (ft: FieldType) => string;
  let fieldTypeHeader: { key: string; value: string; }[];
  let expandedRowIds: any[] = [];

  function addNewFieldType() {
    const fieldId = makeObjectId();
    const ft = new FieldType({ id: fieldId, active: true });
    if (filetype.format == FileType_Format.FLAT_FILE_DELIMITED && !filetype.hasHeader) {
      ft.fieldLocation.case = 'columnIndex';
      ft.fieldLocation.value = Math.max(
          Math.max(... recordtype.fieldTypes.map(
              (ft) => ft.fieldLocation.value as number + 1)),
          1);
    };
    recordtype.fieldTypes.push(ft);
    recordtype.fieldTypes = recordtype.fieldTypes;

    // Automatically expand the new field type row
    expandedRowIds.push(fieldId);
    expandedRowIds = expandedRowIds;
  }

  // Make the table configuration (ie, header and column definition) reactive
  // to the file format.
  function resetTable(filetypeFormat: FileType_Format) {
    if (filetype.format === FileType_Format.FLAT_FILE_DELIMITED) {
      locationHeader = 'CSV Header Column';
      locationValueFn = function(ft: FieldType): string {
        return (ft.fieldLocation.value as string) || '';
      }
    } else if (filetype.format === FileType_Format.FLAT_FILE_FIXED_WIDTH) {
      locationHeader = 'Character Position';
      locationValueFn = function(ft: FieldType): string {
        const range = ft.fieldLocation.value as FixedWidthFieldRange;
        const length = (range.start && range.end)
            ? ` (${range.end - range.start + 1} chars)` : '';
        return `${range.start || '?'} - ${range.end || '?'}${length}`;
      }
    }

    fieldTypeHeader = [
      {key: "fieldName", value: "Field Name" },
      {key: "columnName", value: locationHeader },
      {key: "validations", value: "Validations" },
    ];
  }
  $: resetTable(filetype.format);


  function functionDisp(func: FunctionConfig): string {
    return `${functionsMap.get(func.functionId)?.name}()`;
  }

  $: fieldRows = recordtype.fieldTypes.map((ft, idx) => ({
      id: ft.id,
      // Can't bind to variables declared by let (in the DataTable) so this
      // allows us to bind to `rows` items directly based on the idx from the
      // row
      idx: idx,
      // Create a default for the table row only, not for the expanded form
      fieldName: ft.name || '[New Field]',
      columnName: locationValueFn(ft),
      // TODO: Return this as an array and do pre-style formatting in the
      // fragment
      validations: ft.validations.map(functionDisp).join(', '),
      ft: ft
  }));
</script>

<Grid>
  <Row>
    <Column
      ><TextInput
        inline
        labelText="Name"
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
    </Row>
  </FormGroup>

  <h3>Fields</h3>

  <div class="local">
    <DataTable
        batchExpansion
        size="short"
        headers={fieldTypeHeader}
        rows={fieldRows}
        bind:expandedRowIds>
      <svelte:fragment slot="expanded-row" let:row>
        <FieldTypeSubForm bind:fieldtype={fieldRows[row.idx].ft} {filetype} />
      </svelte:fragment>
    </DataTable>
  </div>


  <Button
    kind="secondary"
    iconDescription="Add New Field Type"
    icon={Add}
    on:click={addNewFieldType}
  >Add New Field Type</Button>
</Grid>


<style>
  .local :global(.bx--data-table tbody tr),
  .local :global(.bx--data-table tbody tr:hover),
  .local :global(.bx--data-table tbody tr td),
  .local :global(.bx--data-table tbody tr td:hover),
  .local :global(.bx--data-table tbody
      tr.bx--parent-row.bx--expandable-row:hover+tr[data-child-row] td) {
    background: white;
  }

</style>
