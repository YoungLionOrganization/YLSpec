// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import initialize from '../wasm/core.mjs';
import {makeClient} from './model.mjs';
const decoder = new TextDecoder('utf-8');
const codes = ['ok', 'invalid', 'syntax', 'limit', 'memory', 'frame', 'unsupported', 'io', 'profile'];
/** Each factory owns a separate WASM instance. Pass wasmBinary for custom bundlers. */
export async function createClient(options = {}) {
  const module = await initialize(options.wasmBinary ? {wasmBinary: options.wasmBinary} : {});
  return makeClient((operation, input, offset, limits) => {
    const pointer = module._malloc(Math.max(1, input.length));
    if (!pointer) throw new Error('Cannot allocate WebAssembly input');
    try {
      module.HEAPU8.set(input, pointer);
      const status = module._yl_web_process(operation, pointer, input.length, offset, limits.maxDocumentBytes, limits.maxDepth);
      if (status) {
        const address = module._yl_web_message(); let end = address;
        while (module.HEAPU8[end] !== 0) end++;
        const error = new Error(decoder.decode(module.HEAPU8.subarray(address, end)));
        Object.assign(error, {code: codes[status], offset: module._yl_web_offset(), line: module._yl_web_line(), column: module._yl_web_column()}); throw error;
      }
      return module.HEAPU8.slice(module._yl_web_data(), module._yl_web_data() + module._yl_web_size());
    } finally {module._free(pointer);}
  }, 'wasm', '0.1.1');
}
