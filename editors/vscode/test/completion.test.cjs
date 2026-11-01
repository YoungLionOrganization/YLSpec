// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const {complete, MAX_COMPLETION_CHARS} = require('../src/completion.cjs');

function suggestions(source, options) {
  const offset = source.indexOf('|');
  assert.notEqual(offset, -1);
  return complete(source.replace('|', ''), offset, options);
}
function labels(source, options) {return suggestions(source, options).map(item => item.label);}
function applied(source, label) {
  const item = suggestions(source).find(item => item.label === label);
  assert.ok(item, `Missing ${label} for ${source}`);
  const text = source.replace('|', '');
  return text.slice(0, item.start) + item.insertText + text.slice(item.end);
}

test('empty and partial table headers offer legal paths without duplicate brackets', () => {
  assert.deepEqual(labels('[|]').slice(0, 3), ['_ylspec', 'data', 'extensions']);
  assert.equal(applied('[da|ta]', 'data'), '[data]');
  assert.equal(applied('[da|', 'data'), '[data]');
  assert.equal(applied('  [da|] # keep', 'data'), '  [data] # keep');
  assert.ok(labels('[extensions.|]').includes('extensions.namespace'));
  assert.ok(labels('[data.network.|]').includes('data.network.section'));
  assert.equal(applied('[extensions."xyz.example".|]', 'extensions."xyz.example".section'), '[extensions."xyz.example".${1:section}]');
  assert.ok(labels('[[|]]').includes('data.items'));
  assert.equal(applied('[[data.it|]]', 'data.items'), '[[data.${1:items}]]');
});

test('defined tables are not redefined and repeated array-table paths remain available', () => {
  assert.ok(!labels('[_ylspec]\nversion="0.1"\n[|]').includes('_ylspec'));
  assert.ok(labels('[data."network settings".tls]\nx=1\n[data.|]').includes('data."network settings"'));
  assert.ok(labels('[[data.workers]]\nname="one"\n[[data.|]]').includes('data.workers'));
  assert.ok(!labels('[data]\ntext="""\n[extensions.fake]\n"""\n[|]').includes('extensions.fake'));
});

test('metadata keys suppress duplicates and preserve an existing assignment', () => {
  assert.ok(labels('[_ylspec]\npro|').includes('profile_version'));
  assert.ok(labels('["_ylspec"]\npro|').includes('profile'));
  assert.ok(!labels('[_ylspec]\nversion="0.1"\n|').includes('version'));
  assert.equal(applied('[_ylspec]\npro|file = "core.data"', 'profile'), '[_ylspec]\nprofile = "core.data"');
  assert.equal(applied('[_ylspec]\npro|', 'profile'), '[_ylspec]\nprofile = "core.data"');
  assert.ok(!labels('[_ylspec.nested]\npro|').includes('profile'));
  assert.ok(labels('_ylspec = { pro| }').includes('profile'));
});

test('boolean completion replaces the entire partial token and preserves surrounding text', () => {
  assert.deepEqual(labels('[data]\nenabled=t|'), ['true', 'time', 'timestamp']);
  assert.equal(applied('[data]\nenabled=t|rue # retain', 'true'), '[data]\nenabled=true # retain');
  assert.equal(applied('[data]\nenabled=f|', 'false'), '[data]\nenabled=false');
  assert.ok(labels('[data]\nenabled=|').includes('false'));
  assert.ok(labels('[data]\nflags=[|]').includes('true'));
  assert.ok(labels('[data]\nflags=[true,\n# next flag\n |]').includes('false'));
  assert.ok(labels('[data]\noptions={enabled=t|}').includes('true'));
  assert.equal(applied('[data]\n"😀enabled"=t|rue', 'true'), '[data]\n"😀enabled"=true');
});

test('metadata values are limited to supported defaults and explicitly configured profiles', () => {
  assert.deepEqual(labels('[_ylspec]\nversion=|'), ['"0.1"']);
  assert.equal(applied('[_ylspec]\nversion="0|.1"', '"0.1"'), '[_ylspec]\nversion="0.1"');
  assert.deepEqual(labels('[_ylspec]\nrequires=|'), ['[]']);
  assert.deepEqual(labels('[_ylspec]\nrequires=[|]'), []);
  assert.ok(labels('[_ylspec]\nprofile="ex|"', {profiles: ['example.manifest']}).includes('"example.manifest"'));
  assert.deepEqual(labels('_ylspec = {version=|}'), ['"0.1"']);
});

test('suggestions stay out of comments, strings, completed values, and arbitrary inline keys', () => {
  for (const source of ['# [|]', '[data]\ntext="[|]"', '[data]\ntext="""\n[|]\n"""',
    "[data]\ntext='''\n[|]\n'''", '[data]\ntext="escaped\\\"[|]"', '[data]\nvalue=true |',
    '[data]\nvalue=[]|', '[data]\nvalue={key=1}|', '[data]\nvalue={ke|}', '[data]\n# enabled=t|']) {
    assert.deepEqual(labels(source), [], source);
  }
  assert.deepEqual(complete(' '.repeat(MAX_COMPLETION_CHARS + 1), 0), []);
});
