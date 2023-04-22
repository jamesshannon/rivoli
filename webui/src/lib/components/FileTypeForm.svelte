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

  import {
    FileType,
    RecordType,
    FieldType,
    FileType_Format,
    FileType_RequireReview
  } from '$lib/protos/config_pb';
  import type { Function } from '$lib/protos/functions_pb';
  import StringList from '$lib/components/StringList.svelte';
  import StringMapping from '$lib/components/StringMapping.svelte';
  import RecordTypeSubForm from '$lib/components/PartnerForm/RecordTypeSubForm.svelte';

  export let filetype: FileType;
  export let showRecordTypes: boolean = false;

  export let functionsMap: Map<string, Function> | null = null;
  const dispatch = createEventDispatcher();
  setContext('FUNCTIONS', functionsMap);

  let formatDropdownItems = [
    { id: FileType_Format.FLAT_FILE_DELIMITED, text: 'Delimited' }
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

  if (!filetype.id) {
    // New record -- set defaults
    filetype.format = FileType_Format.FLAT_FILE_DELIMITED;
  }

  function submitHandler() {
    dispatch('submit', { filetype: filetype });
  }
</script>

<div class="local">
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
          <FormLabel>File Type Tags</FormLabel>
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
        {/if}
      </FormGroup>

      <FormGroup legendText="Filename Filtering & Parsing">
        <Row>
          Filenames are detected and copied based on their filename.
          Additionally, you can parse the filename (using regexp patterns) to
          calculate file-level values, including parsing the file date from the
          filename and arbitary tags.
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
              bind:value={filetype.filenameDateRegexp}
            />
          </Column>
          <Column>
            <TextInput
              labelText="Filename Date Format"
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
