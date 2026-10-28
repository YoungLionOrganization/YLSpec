// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const {tableAt, errorPosition} = require('../src/metadata.cjs');
test('metadata suggestions ignore multiline strings and nested tables', () => {
  assert.equal(tableAt('[_ylspec]\npro'), '_ylspec');
  assert.equal(tableAt('["_ylspec"]\npro'), '_ylspec');
  assert.equal(tableAt('[data]\nx = """\n[_ylspec]\n"""\npro'), '');
  assert.equal(tableAt("[data]\nx = '''\n[_ylspec]\n'''\npro"), '');
  assert.equal(tableAt('[_ylspec]\nx = "incomplete'), '');
  assert.equal(tableAt('[_ylspec]\n[data.nested]\npro'), '');
  assert.equal(tableAt('# [_ylspec]\npro'), '');
});
test('UTF-8 diagnostic columns translate to UTF-16 positions', () => {
  assert.deepEqual(errorPosition('x\n😀é?', {line: 2, column: 7}), {line: 1, character: 3});
  assert.deepEqual(errorPosition('x', {line: 999, column: 999}), {line: 0, character: 1});
});
test('TextMate grammar tokenizes TOML 1.1 strings, dates, and comments', async () => {
  const tm = require('vscode-textmate'), onig = require('vscode-oniguruma');
  const wasm = readFileSync(require.resolve('vscode-oniguruma/release/onig.wasm'));
  await onig.loadWASM(wasm.buffer.slice(wasm.byteOffset, wasm.byteOffset + wasm.byteLength));
  const registry = new tm.Registry({onigLib: Promise.resolve({createOnigScanner: sources => new onig.OnigScanner(sources), createOnigString: source => new onig.OnigString(source)}), loadGrammar: async () => tm.parseRawGrammar(readFileSync(path.join(__dirname, '../syntaxes/ylspec.tmLanguage.json'), 'utf8'), 'ylspec.json')});
  const grammar = await registry.loadGrammar('source.ylspec');
  const scopes = line => grammar.tokenizeLine(line).tokens.flatMap(token => token.scopes);
  assert.ok(scopes('enabled = true # note').includes('constant.language.boolean.ylspec'));
  assert.ok(scopes('stamp = 2026-10-29T12:00:00.123456789Z').includes('constant.other.datetime.ylspec'));
  assert.ok(scopes('name = "# text"').includes('string.quoted.double.ylspec'));
  assert.ok(!scopes('name = "# text"').includes('comment.line.number-sign.ylspec'));
  const multiline = grammar.tokenizeLine('text = """first');
  assert.ok(grammar.tokenizeLine('# still string', multiline.ruleStack).tokens.every(token => token.scopes.includes('string.quoted.triple.double.ylspec')));
  registry.dispose();
});
