import { promises as fsp } from 'fs';
import * as path from 'path';

import { env } from '$env/dynamic/private';

import { db, getOne } from '$lib/server/db';

import { createTask } from '$lib/helpers/celery';

import { makeObjectId } from '$lib/helpers/utils';

import { json } from '@sveltejs/kit';

export async function POST({ request }) {
  let formData = await request.formData();
  let file = formData.get('file') as File;

  let tempFileName = `${Math.floor(Date.now() / 1000)}-${makeObjectId()}`;
  let tempDir =  path.join(env.FILES_BASE, env.FILES_UPLOAD);
  let tempFilePath = path.join(tempDir, tempFileName);

  await fsp.mkdir(tempDir, {recursive: true});

  fsp.writeFile(tempFilePath, file.stream());

  createTask(
    'rivoli.copier',
    'copy_from_upload',
    [file.name, tempFileName, formData.get('partnerId'),
        formData.get('filetypeId')]
  );

  return json({
    status: 'success',
    data: { message: 'File uploaded and scheduled copy.' }
  });
}
