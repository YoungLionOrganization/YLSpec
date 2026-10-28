// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const {parentPort} = require('node:worker_threads');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const engine = import(pathToFileURL(path.join(__dirname, '../engine/src/web.mjs')).href)
  .then(({createClient}) => createClient({wasmBinary: readFileSync(path.join(__dirname, '../engine/wasm/core.wasm'))}));
parentPort.on('message', async ({id, text, limits, format}) => {
  try {
    const yl = await engine;
    const document = yl.loads(text, {limits});
    let issue;
    try {yl.validate(document);}
    catch (error) {issue = {message: error.message, code: error.code, line: error.line, column: error.column, warning: error.code === 'unsupported' && error.message.startsWith('Unsupported profile:')};}
    const formatted = format ? yl.dumps(document) : undefined;
    parentPort.postMessage({id, issue, formatted});
  } catch (error) {
    parentPort.postMessage({id, issue: {message: error.message, code: error.code || 'internal', line: error.line, column: error.column, warning: false}});
  }
});
