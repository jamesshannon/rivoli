import type { FileType, RecordType, FieldType } from '$lib/protos/config_pb';

function makeNodeRecordType(rt: RecordType) {
  return {
    id: ''
  };
}

function makeNodeFieldType(rtId: string, ft: FieldType) {
  return {
    id: `${rtId}-FT-${ft.id}`,
    type: ''
  };
}

class Node {
  id = '';
  type = '';

  inputs: Array<Node> = [];
  outputs: Array<Node> = [];

  constructor(id: string, type: string) {
    this.type = '';
  }

  addInput(input: Node) {
    this.inputs.push(input);
  }

  addOutput(output: Node) {
    this.outputs.push(output);
  }
}

class RecordTypeNodeLoad extends Node {
  constructor(rt: RecordType) {
    super();

    this.id = '';
  }
}

class RecordTypeNode extends Node {
  constructor(rt: RecordType) {
    super(`RT-${rt.id}`, 'Record');

    // just create the nodes here. Make avaialble as properties?
  }
}

for (let rt of filetype.recordTypes) {
  let rtLoad = new RecordTypeNode(rt);
  let rtId = `RT-${rt.id}`;
  let rtIdLoad = `${rtId}-LOAD`;
  let rtIdCombined = `${rtId}-COMBINED`;
  let rtIdEnd = `${rtId}-END`;

  vertices.set(rtIdLoad, {});
  edges.push(['INPUT', rtIdLoad]);

  // Create the "complete record" vertice now; the field -> combined edges
  // can be added later after the last field-level validation
  vertices.set(rtIdCombined, {});

  for (let ft of rt.fieldTypes) {
    let ftId = `${rtId}-FT-${ft.id}`;
    vertices.set(ftId, {});
    edges.push([rtIdLoad, ftId]);

    let lastId = ftId;

    for (let validation of ft.validations) {
      let vId = `${ftId}-${validation.id}`;
      vertices.set(vId, {});
      edges.push([lastId, vId]);

      lastId = vId;
    }

    // lastId is either the field ID or the most recent validation ID
    edges.push([lastId, rtIdCombined]);
  }

  let lastId = rtIdCombined;

  for (let validation of rt.validations) {
    let vId = `${rtId}-VAL-${validation.id}`;
    vertices.set(vId, {});
    edges.push([lastId, vId]);

    lastId = vId;
  }

  if (rt.upload) {
    let uploadId = `${rtId}-UP-${rt.upload.id}`;
    vertices.set(uploadId, {});
    edges.push([lastId, uploadId]);

    lastId = uploadId;
  }

  vertices.set(rtIdEnd, {});
  edges.push([lastId, rtIdEnd]);
}

console.log(vertices);
console.log(edges);

export function makeFileTypeGraph(ft: FileType): any {
  const vertices = new Map<string, Node>();
  const edges = [];

  vertices.set('INPUT', new Node('INPUT', 'GENERIC'));

  for (let rt of ft.recordTypes) {
    let rtNode = new RecordTypeNode(rt);
  }
}
