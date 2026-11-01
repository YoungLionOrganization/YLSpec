// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const {fields} = require('./metadata.cjs');
const MAX_COMPLETION_CHARS = 1024 * 1024;

/** Tolerant editor lexer. Positions are UTF-16 offsets, including unfinished tokens.
 * This supplies suggestions only; document validity belongs to the C parser.
 */
function lex(text) {
  const tokens = [];
  for (let i = 0; i < text.length;) {
    const start = i, ch = text[i];
    if (ch === ' ' || ch === '\t' || ch === '\r') {i++; continue;}
    if (ch === '#') {
      while (i < text.length && text[i] !== '\n') i++;
      tokens.push({kind: 'comment', start, end: i, text: text.slice(start, i)}); continue;
    }
    if (ch === '"' || ch === "'") {
      const triple = text.slice(i, i + 3) === ch.repeat(3), width = triple ? 3 : 1;
      i += width;
      let closed = false;
      while (i < text.length) {
        if (ch === '"' && text[i] === '\\') {i = Math.min(text.length, i + 2); continue;}
        if (text.slice(i, i + width) === ch.repeat(width)) {
          i += width;
          if (triple) while (i < text.length && text[i] === ch) i++;
          closed = true; break;
        }
        if (!triple && text[i] === '\n') break;
        i++;
      }
      tokens.push({kind: 'string', start, end: i, text: text.slice(start, i), closed, triple}); continue;
    }
    if ('[]=,.{}\n'.includes(ch)) {i++; tokens.push({kind: ch, start, end: i, text: ch}); continue;}
    while (i < text.length && !/[\s\[\]=,.{}#"']/.test(text[i])) i++;
    if (i === start) i++;
    tokens.push({kind: 'atom', start, end: i, text: text.slice(start, i)});
  }
  return tokens;
}

function keyText(token) {
  if (token.kind === 'atom' && /^[A-Za-z0-9_-]+$/.test(token.text)) return token.text;
  if (token.kind !== 'string' || !token.closed || token.triple) return undefined;
  if (token.text[0] === "'") return token.text.slice(1, -1);
  try {return JSON.parse(token.text.replace(/\\x([a-fA-F0-9]{2})/g, '\\u00$1').replace(/\\e/g, '\\u001b'));}
  catch {return undefined;}
}
function keyPath(tokens) {
  const path = [];
  for (let i = 0; i < tokens.length; i++) {
    if (i % 2) {if (tokens[i].kind !== '.') return undefined;}
    else {const key = keyText(tokens[i]); if (key === undefined) return undefined; path.push(key);}
  }
  return tokens.length && tokens.length % 2 ? path : undefined;
}
function displayPath(path) {return path.map(key => /^[A-Za-z0-9_-]+$/.test(key) ? key : JSON.stringify(key)).join('.');}

/** Split complete logical statements without treating array contents as headers. */
function statements(tokens) {
  const result = [];
  let current = [], depth = 0;
  for (const token of tokens) {
    if (token.kind === 'comment') continue;
    if (token.kind === '\n' && (depth === 0 || current[0]?.kind === '[')) {
      if (current.length) {current.finished = true; result.push(current);}
      current = []; depth = 0; continue;
    }
    if (token.kind === '\n') continue;
    current.push(token);
    if (token.kind === '[' || token.kind === '{') depth++;
    if (token.kind === ']' || token.kind === '}') depth = Math.max(0, depth - 1);
  }
  if (current.length) result.push(current);
  return result;
}
function headerPath(tokens) {
  const width = tokens[1]?.kind === '[' ? 2 : 1;
  if (tokens[0]?.kind !== '[' || tokens.at(-1)?.kind !== ']' || (width === 2 && tokens.at(-2)?.kind !== ']')) return;
  const path = keyPath(tokens.slice(width, -width));
  return path && {path, array: width === 2};
}

function complete(text, offset, options = {}) {
  if (text.length > MAX_COMPLETION_CHARS || offset < 0 || offset > text.length) return [];
  const tokens = lex(text), before = lex(text.slice(0, offset));
  const last = before.at(-1);
  if (last?.kind === 'comment' && last.end === offset) return [];
  let table = [], current = [];
  for (const statement of statements(before)) {
    const header = headerPath(statement);
    const finished = statement.finished;
    // A closed header remains the current context on its own line.
    if (header && finished) table = header.path;
    else current = statement;
    if (finished) current = [];
  }
  const all = statements(tokens), usedTables = new Set(), usedMetadata = new Set();
  let scope = [];
  for (const statement of all) {
    const header = headerPath(statement);
    if (header) {
      scope = header.path;
      if (!(statement[0].start <= offset && offset <= statement.at(-1).end)) usedTables.add(displayPath(scope));
    } else if (scope.length === 1 && scope[0] === '_ylspec') {
      const equals = statement.findIndex(token => token.kind === '='), path = keyPath(statement.slice(0, equals));
      if (path?.length === 1 && !(statement[0].start <= offset && offset <= (statement[equals]?.end ?? offset))) usedMetadata.add(path[0]);
    }
  }
  const lineStart = text.lastIndexOf('\n', Math.max(0, offset - 1)) + 1;
  const prefix = text.slice(lineStart, offset);
  const fullLineEnd = text.indexOf('\n', offset), lineEnd = fullLineEnd < 0 ? text.length : fullLineEnd;
  const line = text.slice(lineStart, lineEnd);
  if (/^\s*\[/.test(prefix) && current[0]?.kind === '[') {
    const width = /^\s*\[\[/.test(prefix) ? 2 : 1;
    const open = line.indexOf('['), start = lineStart + open + width;
    // Headers use a dedicated edit spanning their complete interior, including quotes/dots.
    let end = lineEnd;
    for (const token of tokens) if (token.start >= offset && token.start < lineEnd && (token.kind === ']' || token.kind === 'comment')) {end = token.start; break;}
    const closing = text.slice(end, end + width) === ']'.repeat(width) ? '' : ']'.repeat(width);
    const typed = text.slice(start, offset).trim();
    const candidates = width === 2 ? [] : [
      ['_ylspec', '_ylspec', 'Reserved format and profile metadata'],
      ['data', 'data', 'Application-defined configuration or manifest values'],
      ['extensions', 'extensions', 'Optional namespaced extension tables'],
      ['data.section', 'data.${1:section}', 'Create an application-defined nested table', true],
      ['extensions.namespace', 'extensions."${1:xyz.example}"', 'Create an explicitly namespaced extension table', true]
    ];
    const parentTokens = current.slice(width), parent = keyPath(parentTokens.at(-1)?.kind === '.' ? parentTokens.slice(0, -1) : parentTokens);
    if (parent && ['data', 'extensions'].includes(parent[0]) && (parent.length > 1 || parentTokens.at(-1)?.kind === '.')) {
      const base = displayPath(parent);
      candidates.push([base + '.section', base.replace(/[\\$}]/g, '\\$&') + '.${1:section}', 'Create a nested application table', true]);
    }
    if (width === 2) candidates.push(['data.items', 'data.${1:items}', 'Create an application-defined array of tables', true]);
    for (const statement of all) {
      const header = headerPath(statement);
      if (!header || header.array !== (width === 2)) continue;
      const name = displayPath(header.path);
      if (width === 2 || !usedTables.has(name)) candidates.push([name, name, 'Table path found in this document']);
      // Parent paths help complete extensions. or data. without quoting namespace dots incorrectly.
      for (let i = 1; i < header.path.length; i++) {
        const parent = displayPath(header.path.slice(0, i));
        if (width === 1 && !usedTables.has(parent)) candidates.push([parent, parent, 'Parent table found in this document']);
      }
    }
    return [...new Map(candidates.filter(([label, , , snippet]) => (snippet || width === 2 || !usedTables.has(label)) &&
      (!typed || label.startsWith(typed) || label.startsWith(typed.replace(/['"]/g, '')))).map(([label, insertText, detail, snippet]) =>
      [label, {label, insertText: insertText + closing, detail, snippet, kind: 'Module', start, end, filterText: typed + label}])).values()];
  }
  const equals = current.findIndex(token => token.kind === '=');
  if (equals < 0) {
    if (table.length !== 1 || table[0] !== '_ylspec' || !/^\s*[A-Za-z_]*$/.test(prefix)) return [];
    const start = offset - (/[A-Za-z_]*$/.exec(prefix)?.[0].length || 0);
    let end = offset; while (/[A-Za-z_]/.test(text[end] || '') && end < text.length) end++;
    const hasEquals = /^\s*=/.test(text.slice(end, lineEnd));
    return Object.entries(fields).filter(([key]) => !usedMetadata.has(key)).map(([label, info]) => ({
      label, insertText: hasEquals ? label : `${label} = ${info.value}`, detail: info.detail,
      kind: 'Property', start, end, followup: !hasEquals
    }));
  }
  const path = keyPath(current.slice(0, equals));
  if (!path) return [];
  let valuePath = [...table, ...path], valueStart = current[equals].end;
  const stack = [];
  for (const token of current.slice(equals + 1)) {
    if (token.kind === '{' || token.kind === '[') {
      stack.push({kind: token.kind, path: valuePath, keys: []}); valueStart = token.end;
    } else if (token.kind === '}' || token.kind === ']') {
      const frame = stack.pop(); if (!frame) return [];
      valuePath = frame.path; valueStart = token.end;
    } else if (token.kind === ',') {
      if (!stack.length) return [];
      const frame = stack.at(-1); frame.keys = []; valuePath = frame.path; valueStart = token.end;
    } else if (stack.at(-1)?.kind === '{') {
      const frame = stack.at(-1);
      if (token.kind === '=') {const keys = keyPath(frame.keys); if (!keys) return []; valuePath = [...frame.path, ...keys]; valueStart = token.end;}
      else if (valuePath === frame.path) frame.keys.push(token);
    }
  }
  const frame = stack.at(-1);
  if (['}', ']'].includes(current.at(-1)?.kind)) return [];
  if (frame?.kind === '{' && valuePath === frame.path) {
    if (frame.path.length !== 1 || frame.path[0] !== '_ylspec') return [];
    const part = text.slice(valueStart, offset), word = /[A-Za-z_]*$/.exec(part)[0];
    if (!/^\s*[A-Za-z_]*$/.test(part)) return [];
    return Object.entries(fields).filter(([key]) => !new RegExp('(?:^|[, {])' + key + '\\s*=').test(text.slice(current[equals].end, offset)))
      .map(([label, info]) => ({label, insertText: `${label} = ${info.value}`, detail: info.detail, kind: 'Property', start: offset - word.length, end: offset}));
  }
  const valueTokens = current.filter(token => token.start >= valueStart);
  const sourceStart = valueTokens[0]?.start ?? offset;
  const raw = text.slice(sourceStart, offset), trimmed = raw.trimStart(), start = offset - trimmed.length;
  const isMetadata = valuePath.length === 2 && valuePath[0] === '_ylspec';
  const key = isMetadata ? valuePath[1] : '';
  let end = offset;
  const active = tokens.find(token => token.start <= start && start < token.end);
  if (active && active.start === start) end = active.end;
  if (last?.kind === 'string' && last.end === offset && !last.closed && !['version', 'profile', 'profile_version'].includes(key)) return [];
  if (trimmed && !/^[A-Za-z_+-]*$/.test(trimmed) && !(isMetadata && /^['"][^'"\n]*['"]?$/.test(trimmed))) return [];
  // A completed value or collection requires a comma/new assignment before more suggestions.
  if (trimmed && /\s$/.test(raw)) return [];
  const make = (label, insertText, detail, snippet = false, kind = 'Value') => ({label, insertText, detail, snippet, kind, start, end});
  if (isMetadata) {
    if (key === 'version' || key === 'profile_version') return [make('"0.1"', '"0.1"', fields[key].detail)];
    if (key === 'profile') return [...new Set(['core.data', ...(options.profiles || [])])].map(value => make(JSON.stringify(value), JSON.stringify(value), fields.profile.detail));
    if (key === 'requires') return trimmed || stack.length ? [] : [make('[]', '[]', 'No mandatory features; add only features understood by your reader')];
    return [];
  }
  return [
    make('true', 'true', 'TOML boolean: enabled / true', false, 'Constant'),
    make('false', 'false', 'TOML boolean: disabled / false', false, 'Constant'),
    make('string', '"${1:text}"', 'UTF-8 text string', true, 'Snippet'),
    make('array', '[${1}]', 'Array of TOML values', true, 'Snippet'),
    make('inline table', '{ ${1:key} = ${2:value} }', 'Inline table of application-defined values', true, 'Snippet'),
    make('integer', '${1:0}', 'Signed 64-bit integer', true, 'Snippet'),
    make('float', '${1:0.0}', 'IEEE-754 binary64 floating-point number', true, 'Snippet'),
    make('date', '${1:2026}-${2:01}-${3:01}', 'Local date: YYYY-MM-DD', true, 'Snippet'),
    make('time', '${1:12}:${2:00}:${3:00}', 'Local time: HH:MM:SS', true, 'Snippet'),
    make('timestamp', '${1:2026}-${2:01}-${3:01}T${4:12}:${5:00}:${6:00}Z', 'Offset timestamp with exact fractional precision', true, 'Snippet'),
    make('inf', 'inf', 'Positive floating-point infinity', false, 'Constant'),
    make('nan', 'nan', 'Floating-point not-a-number', false, 'Constant')
  ].filter(item => !trimmed || item.label.startsWith(trimmed));
}

module.exports = {complete, MAX_COMPLETION_CHARS};
