// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {createClient} from '../src/index.mjs';
const yl = await createClient();
test('native typed values preserve int64, temporal precision, and safe keys', () => {
  assert.equal(yl.backend, 'node-api');
  const doc = new yl.Document({integer: 9223372036854775807n, float: 1, value: 'Hello 🌍', stamp: new yl.TemporalValue('datetime-offset', '2026-10-28T12:34:56.123456789Z')});
  const restored = yl.loads(yl.dumps(doc));
  assert.equal(restored.data.integer, 9223372036854775807n); assert.equal(restored.data.float, 1);
  assert.equal(restored.data.stamp.text, doc.data.stamp.text);
  const malicious = yl.loads("_ylspec={version='0.1',profile='core.data',profile_version='0.1'}\n[data]\n'__proto__'={polluted=true}");
  assert.equal(Object.getPrototypeOf(malicious.data), null); assert.equal({}.polluted, undefined);
});
test('frame offsets and bounded reads', async () => {
  const frame = yl.pack(new yl.Document({name: 'embedded'})); const host = new Uint8Array(frame.length + 9); host.set(frame, 7);
  assert.equal(yl.unpack(host, 7).data.name, 'embedded');
  const reads = []; const doc = await yl.readAt((position, size) => {reads.push([position, size]); return host.slice(Number(position), Number(position) + size);}, 7n, BigInt(frame.length));
  assert.equal(doc.data.name, 'embedded'); assert.deepEqual(reads, [[7n, 32], [39n, frame.length - 32]]);
  for (let i = 0; i < frame.length; i++) assert.throws(() => yl.unpack(frame.slice(0, i)));
});
test('errors, profiles, cyclic inputs, and CommonJS', async () => {
  assert.throws(() => yl.loads('invalid'), yl.YLSpecError);
  const doc = new yl.Document({}, {profile: 'xyz.example', profileVersion: '1'});
  assert.throws(() => yl.validate(doc), /Unsupported profile/);
  yl.validate(doc, {validators: new Map([['xyz.example@1', () => true]])});
  const cycle = {}; cycle.self = cycle; assert.throws(() => yl.dumps(new yl.Document(cycle)), /Cyclic/);
  const cjs = createRequire(import.meta.url)('../src/index.cjs'); assert.equal((await cjs.createClient()).backend, 'node-api');
});

test('multiple frames and rejected headers never read unrelated payloads', async () => {
  const first = yl.pack(new yl.Document({name: 'first'})), second = yl.pack(new yl.Document({name: 'second'}));
  const host = new Uint8Array(7 + first.length + second.length + 9); host.set(first, 7); host.set(second, 7 + first.length);
  assert.equal(yl.unpack(host, 7).data.name, 'first'); assert.equal(yl.unpack(host, 7 + first.length).data.name, 'second');
  for (const change of [header => {header[0] = 0;}, header => {header[28] = 1;}, header => {new DataView(header.buffer).setBigUint64(16, (1n << 64n) - 1n, true);}]) {
    const header = first.slice(0, 32); change(header); let reads = 0;
    await assert.rejects(yl.readAt((_offset, size) => {reads++; assert.equal(size, 32); return header;}, 0n, BigInt(first.length)), yl.YLSpecError);
    assert.equal(reads, 1);
  }
  await assert.rejects(yl.readAt(() => new Uint8Array(0), (1n << 64n) - 16n, 32n), RangeError);
  const limited = new yl.Document({nested: {value: true}}, {limits: {maxDepth: 2}});
  assert.throws(() => yl.dumps(limited), /depth/i);
});
