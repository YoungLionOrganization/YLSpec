// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {makeClient} from './model.mjs';
const require = createRequire(import.meta.url);
const libc = process.platform === 'linux' ? (process.report.getReport().header.glibcVersionRuntime ? '-gnu' : '-musl') : '';
const target = `${process.platform}-${process.arch}${libc}`;
const path = fileURLToPath(new URL(`../prebuilds/${target}/ylspec.node`, import.meta.url));
let addon;
try {addon = require(path);} catch (error) {throw new Error(`YLSpec native module unavailable for ${target}. Use the WebAssembly entry point for an unsupported host. ${error.message}`, {cause: error});}
const metadata = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const client = makeClient((op, input, offset, limits) => new Uint8Array(addon.process(op, Buffer.from(input), offset, limits.maxDocumentBytes, limits.maxDepth)), 'node-api', metadata.version);
export default client;
