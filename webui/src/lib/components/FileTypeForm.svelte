<script lang="ts">
  import { createEventDispatcher, setContext } from 'svelte';

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
    TextInput
  } from 'carbon-components-svelte';
  import Add from 'carbon-icons-svelte/lib/Add.svelte';
  import ColumnDependency from "carbon-icons-svelte/lib/ColumnDependency.svelte";

  import { makeObjectId } from '$lib/helpers/utils';

  import {
    FileType,
    RecordType,
    FileType_Format,
    FileType_RequireReview,
    Output,
    OutputConfiguration,
    DestinationFile
  } from '$lib/rivoli/protos/config_pb';
  import type { Function } from '$lib/rivoli/protos/functions_pb';

  import Diagram from '$lib/components/FileProcessing/Diagram.svelte';
  import StringList from '$lib/components/StringList.svelte';
  import StringMapping from '$lib/components/StringMapping.svelte';
  import RecordTypeSubForm from '$lib/components/PartnerForm/RecordTypeSubForm.svelte';
  import OutputSubForm from './PartnerForm/OutputSubForm.svelte';

  export let filetype: FileType;
  export let showRecordTypes: boolean = false;

  export let functionsMap: Map<string, Function>;
  const dispatch = createEventDispatcher();
  setContext('FUNCTIONS', functionsMap);

  let formatDropdownItems = [
    { id: FileType_Format.FLAT_FILE_DELIMITED, text: 'Delimited' },
    { id: FileType_Format.FLAT_FILE_FIXED_WIDTH, text: 'Fixed-Width' }
  ];
  let reviewDropdownItems = [
    {
      id: FileType_RequireReview.REQUIRE_UNKNOWN,
      text: "Don't Require Review"
    },
    { id: FileType_RequireReview.ON_ERRORS, text: 'On Any Errors' },
    { id: FileType_RequireReview.ALWAYS, text: 'Always' }
  ];

  function addNewRecordType() {
    filetype.recordTypes.push(new RecordType());
    filetype.recordTypes = filetype.recordTypes;
  }

  function addNewOutput() {
    filetype.outputs.push(
      new Output({
        id: makeObjectId(),
        active: true,
        configuration: new OutputConfiguration(),
        file: new DestinationFile()
      })
    );
    filetype.outputs = filetype.outputs;
  }

  if (!filetype.id) {
    // New record -- set defaults
    filetype.format = FileType_Format.FLAT_FILE_DELIMITED;
  }

  function submitHandler() {
    dispatch('submit', { filetype: filetype });
  }
</script>

<div class="local">
{#if false}
  <Button kind="tertiary" icon={ColumnDependency} />

  <div style="width: 100%; height: 500px;">
  <Diagram
        {filetype}
        functions={functionsMap}
      />
  </div>
  {/if}


  <Form on:submit={submitHandler}>
    <Grid>
      <Row>Description of a filetype</Row>
      <Row>
        <Column
          ><TextInput
            bind:value={filetype.name}
            labelText="File Type Name"
          /></Column
        >
        <Column>
          <Checkbox labelText="Active" bind:checked={filetype.active} />
        </Column>
      </Row>
      <Row>
        <Column>
          <FormLabel>File Type Parameters</FormLabel>
          <StringMapping bind:staticTags={filetype.staticTags} />
        </Column>
        <Column>
          <Dropdown
            titleText="Require Review Before Uploading"
            bind:selectedId={filetype.requireUploadReview}
            items={reviewDropdownItems}
          />
        </Column>
      </Row>

      <FormGroup legendText="File Format">
        <Row>
          <Column>
            <Dropdown
              titleText="Format"
              bind:selectedId={filetype.format}
              items={formatDropdownItems}
            />
          </Column>
          <Column />
        </Row>
        {#if filetype.format === FileType_Format.FLAT_FILE_DELIMITED}
          <Row>
            <Column>
              <Checkbox
                labelText="File has header"
                bind:checked={filetype.hasHeader}
              />
            </Column>
            <Column>
              <TextInput
                labelText="Column Separator"
                bind:value={filetype.delimitedSeparator}
              />
            </Column>
          </Row>
        {:else if filetype.format === FileType_Format.FLAT_FILE_FIXED_WIDTH}
          <!-- No settings for fixed-width files. -->
        {/if}
      </FormGroup>

      <FormGroup legendText="Filename Filtering & Parsing">
        <Row>
          Filenames are detected and copied based on their filename.
          Additionally, you can parse the filename (using regexp patterns) to
          calculate file-level values, including parsing the file date from the
          filename and arbitary parameters.
        </Row>
        <Row>
          <Column>
            <FormLabel>Filename Matches</FormLabel>
            At least one of these patterns must match for the file to be copied.
            <StringList bind:strings={filetype.fileMatches} />
          </Column>
          <Column />
        </Row>
        <Row>
          <!-- Configure these fields to parse the date from the filename.<br> -->
          <Column>
            <TextInput
              labelText="Filename Date Regexp"
              helperText="Must capture YEAR, MONTH, and DAY groups"
              bind:value={filetype.filenameDateRegexp}
            />
          </Column>
          <Column>
            <TextInput
              labelText="Filename Date Format"
              helperText="Parses captured date in YEAR-MONTH-DATE. Default is %Y-%m-%d."
              bind:value={filetype.filenameDateFormat}
            />
          </Column>
        </Row>
        <Row>
          <Column>
            <FormLabel>Pattern-based Tag Parsing</FormLabel>
            <StringList bind:strings={filetype.filenameTagRegexps} />
          </Column>
          <Column />
        </Row>
      </FormGroup>

      <FormGroup legendText="Upload Batching">
        <Row>If configured, all uploads will be</Row>
        <Row>
          <Column>
            <NumberInput
              label="Upload Batch Size"
              bind:value={filetype.uploadBatchSize}
            />
          </Column>
          <Column>
            <TextInput
              labelText="Upload Batch GroupBy Key"
              bind:value={filetype.uploadBatchGroupKey}
            />
          </Column>
        </Row>
      </FormGroup>

      {#if showRecordTypes}
        <Row>
          <Column>
            <h2>Record Types</h2>
            <Tabs type="container">
              {#each filetype.recordTypes as recordtype}
                <Tab
                  label={recordtype.name || '[New Record Type]'}
                  href={recordtype.id.toString()}
                />
              {/each}
              <div class="btn-with-thing">
                <Button
                  kind="secondary"
                  iconDescription="Add New Record Type"
                  icon={Add}
                  on:click={addNewRecordType}
                />
              </div>
              <svelte:fragment slot="content">
                {#each filetype.recordTypes as recordtype}
                  <TabContent>
                    <RecordTypeSubForm bind:recordtype {filetype} />
                  </TabContent>
                {/each}
              </svelte:fragment>
            </Tabs>
          </Column>
        </Row>

        <!-- Outputs (Reports) -->
        <Row>
          <Column>
            <h2>Reports</h2>
            <Tabs type="container">
              {#each filetype.outputs as output}
                <Tab
                  label={output.name || '[New Report]'}
                  href={output.id.toString()}
                />
              {/each}
              <div class="btn-with-thing">
                <Button
                  kind="secondary"
                  iconDescription="Add New Report"
                  icon={Add}
                  on:click={addNewOutput}
                />
              </div>
              <svelte:fragment slot="content">
                {#each filetype.outputs as output}
                  <TabContent>
                    <OutputSubForm {filetype} bind:output />
                  </TabContent>
                {/each}
              </svelte:fragment>
            </Tabs>
          </Column>
        </Row>
      {/if}
    </Grid>

    <Button type="submit">Save</Button>
  </Form>
</div>

<style>
  /* the assistive bit in the button causes a weird box on hover */
  div.btn-with-thing
    :global(
      .bx--btn.bx--btn--icon-only.bx--tooltip__trigger .bx--assistive-text
    ) {
    display: none;
  }

  div.local :global(.displaynone) {
    display: none;
  }

  div.local :global(legend) {
    font-size: 1.5rem;
  }
</style>
