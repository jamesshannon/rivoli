import { promises as fsp } from 'fs';
import { basename } from 'path';

import { db, getOne } from '$lib/server/db';

import type { File } from '$lib/rivoli/protos/processing_pb';

export async function GET({ params }) {
  const file = await getOne<File>(
    db.collection('files'),
    parseInt(params.fileid),
    false
  );
  const output = file.outputs.find((o) => o.id == params.outputid);

  const report = await fsp.readFile(output!.outputFilename);

  let fbase = basename(output!.outputFilename);
  return new Response(report, {
    status: 200,
    headers: {
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${fbase}"`
    }
  });
}
