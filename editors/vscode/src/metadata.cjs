// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const fields = Object.freeze({
  version: {value: '"0.1"', detail: 'YLSpec document format version. Independent of the application version.'},
  profile: {value: '"core.data"', detail: 'Profile identifier. Unknown profiles remain readable; validation needs an explicit validator.'},
  profile_version: {value: '"0.1"', detail: 'Version of the selected profile. The generic core.data profile uses 0.1.'},
  requires: {value: '[]', detail: 'Mandatory feature identifiers. Unsupported mandatory features fail validation.'}
});
const template = '[_ylspec]\nversion = "0.1"\nprofile = "core.data"\nprofile_version = "0.1"\n\n[data]\nname = "Example"\n';
/** Track the current table while ignoring comments and single/multiline strings.
 * This only scopes editor suggestions; the C parser decides document validity.
 */
function tableAt(text) {
  let table = '', quote = '', triple = false, lineStart = true;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quote) {
      if (quote === '"' && ch === '\\') {i++; continue;}
      if (triple ? text.slice(i, i + 3) === quote.repeat(3) : ch === quote) {
        i += triple ? 2 : 0; quote = ''; triple = false;
      }
      if (ch === '\n') lineStart = true;
      else lineStart = false;
      continue;
    }
    if (ch === '\n') {lineStart = true; continue;}
    if (ch === '#') {const end = text.indexOf('\n', i); if (end < 0) break; i = end - 1; continue;}
    if (lineStart && /[ \t\r]/.test(ch)) continue;
    if (lineStart && ch === '[') {
      const end = text.indexOf('\n', i), line = text.slice(i, end < 0 ? undefined : end);
      const header = /^\[\s*(?:_ylspec|"_ylspec"|'_ylspec')\s*\]\s*(?:#.*)?$/.test(line);
      table = header ? '_ylspec' : '';
    }
    lineStart = false;
    if (ch === '"' || ch === "'") {quote = ch; triple = text.slice(i, i + 3) === ch.repeat(3); if (triple) i += 2;}
  }
  return quote ? '' : table;
}
/** C columns count UTF-8 bytes. VS Code columns count UTF-16 code units. */
function errorPosition(text, error) {
  const lines = text.split('\n');
  const line = Math.max(0, Math.min(lines.length - 1, (error.line || 1) - 1));
  const source = lines[line], byteColumn = Math.max(0, (error.column || 1) - 1);
  let bytes = 0, character = 0;
  for (const point of source) {
    const next = bytes + Buffer.byteLength(point);
    if (next > byteColumn) break;
    bytes = next; character += point.length;
  }
  return {line, character};
}
module.exports = {fields, template, tableAt, errorPosition};
