// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
/** Shared value model and private binding transport. TOML parsing stays in C. */
const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', {fatal: true});
const kinds = ['date', 'time', 'datetime', 'datetime-offset'];
const codes = ['ok', 'invalid', 'syntax', 'limit', 'memory', 'frame', 'unsupported', 'io', 'profile'];
export const defaultLimits = Object.freeze({maxDocumentBytes: 16777216, maxDepth: 64});
export class YLSpecError extends Error {
  constructor(message, code = 'invalid', position = {}) {
    super(message); this.name = 'YLSpecError'; this.code = code;
    this.offset = position.offset ?? 0; this.line = position.line ?? 0; this.column = position.column ?? 0;
  }
}
export class TemporalValue {
  constructor(kind, text) {
    if (!kinds.includes(kind) || typeof text !== 'string') throw new TypeError('Invalid temporal kind or text');
    this.kind = kind; this.text = text; Object.freeze(this);
  }
}
function limitsOf(value = defaultLimits) {
  const limits = {...defaultLimits, ...value};
  if (!Number.isInteger(limits.maxDocumentBytes) || limits.maxDocumentBytes < 1 || limits.maxDocumentBytes > 2147483647 ||
      !Number.isInteger(limits.maxDepth) || limits.maxDepth < 1 || limits.maxDepth > 128) throw new RangeError('Invalid resource limits');
  return Object.freeze(limits);
}
function utf8(text) {
  for (const character of text) {
    const code = character.codePointAt(0);
    if (code >= 0xd800 && code <= 0xdfff) throw new TypeError('Unpaired UTF-16 surrogate');
  }
  return encoder.encode(text);
}
function toWire(root, limits) {
  const chunks = []; let length = 0; const active = new Set();
  const append = bytes => {length += bytes.length; if (length > limits.maxDocumentBytes * 8 + 1024) throw new YLSpecError('Binding input limit exceeded', 'limit'); chunks.push(bytes);};
  const number = (value, size) => {const data = new Uint8Array(size); const view = new DataView(data.buffer); if (size === 1) data[0] = value; else view.setUint32(0, value, true); append(data);};
  const string = value => {const data = utf8(value); number(data.length, 4); append(data);};
  function write(value, depth) {
    if (depth > limits.maxDepth) throw new YLSpecError('Binding value depth exceeded', 'limit');
    if (value instanceof Date) value = new TemporalValue('datetime-offset', value.toISOString());
    if (typeof value === 'string') {number(0, 1); string(value);}
    else if (typeof value === 'bigint') {
      if (value < -(1n << 63n) || value >= (1n << 63n)) throw new RangeError('Integer exceeds signed 64-bit range');
      number(1, 1); const data = new Uint8Array(8); new DataView(data.buffer).setBigInt64(0, value, true); append(data);
    } else if (typeof value === 'number') {number(2, 1); const data = new Uint8Array(8); new DataView(data.buffer).setFloat64(0, value, true); append(data);}
    else if (typeof value === 'boolean') {number(3, 1); number(Number(value), 1);}
    else if (value instanceof TemporalValue) {number(4, 1); number(kinds.indexOf(value.kind), 1); string(value.text);}
    else if (value !== null && typeof value === 'object') {
      if (active.has(value)) throw new TypeError('Cyclic application data');
      const array = Array.isArray(value);
      if (!array && Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null) throw new TypeError('Expected a plain object or array');
      active.add(value); const keys = array ? value : Object.keys(value);
      if (keys.length > 16384) throw new YLSpecError('Container entry limit exceeded', 'limit');
      number(array ? 5 : 6, 1); number(keys.length, 4);
      if (array) for (const item of value) write(item, depth + 1);
      else for (const key of keys) {string(key); write(value[key], depth + 1);}
      active.delete(value);
    } else throw new TypeError('Unsupported TOML value');
  }
  write(root, 0); const output = new Uint8Array(length); let position = 0;
  for (const chunk of chunks) {output.set(chunk, position); position += chunk.length;} return output;
}
function fromWire(bytes) {
  let position = 0; const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const take = size => {if (size > bytes.length - position) throw new Error('Truncated native value'); const start = position; position += size; return start;};
  const byte = () => view.getUint8(take(1));
  const count = () => view.getUint32(take(4), true);
  const string = () => {const size = count(); return decoder.decode(bytes.subarray(take(size), position));};
  function read(depth) {
    if (depth > 128) throw new Error('Invalid native depth');
    switch (byte()) {
      case 0: return string();
      case 1: return view.getBigInt64(take(8), true);
      case 2: return view.getFloat64(take(8), true);
      case 3: return byte() !== 0;
      case 4: {const kind = kinds[byte()]; return new TemporalValue(kind, string());}
      case 5: {const size = count(); const result = []; for (let i = 0; i < size; i++) result.push(read(depth + 1)); return result;}
      case 6: {const size = count(); const result = Object.create(null); for (let i = 0; i < size; i++) {const key = string(); result[key] = read(depth + 1);} return result;}
      default: throw new Error('Unknown native value type');
    }
  }
  const result = read(0); if (position !== bytes.length) throw new Error('Trailing native bytes'); return result;
}
export class Document {
  constructor(data = {}, options = {}) {
    this.root = {_ylspec: {version: '0.1', profile: options.profile ?? 'core.data', profile_version: options.profileVersion ?? '0.1'}, data: {...data}};
    if (options.extensions) this.root.extensions = {...options.extensions};
    this.limits = limitsOf(options.limits);
  }
  get data() {return this.root.data;}
  get metadata() {return this.root._ylspec;}
  get extensions() {return this.root.extensions ??= Object.create(null);}
}
export function makeClient(process, backend, version) {
  function call(operation, input, offset, limits) {
    try {return process(operation, input, offset, limits);}
    catch (error) {if (codes.includes(error.code)) throw new YLSpecError(error.message, error.code, error); throw error;}
  }
  const restored = (root, limits) => {const result = new Document({}, {limits}); result.root = fromWire(root); return result;};
  const check = document => {if (!(document instanceof Document)) throw new TypeError('Expected Document'); return limitsOf(document.limits);};
  const client = {
    backend, version, Document, TemporalValue, YLSpecError,
    loads(text, options = {}) {if (typeof text !== 'string') throw new TypeError('Expected TOML text'); const limits = limitsOf(options.limits); return restored(call(0, utf8(text), 0, limits), limits);},
    dumps(document) {const limits = check(document); return decoder.decode(call(1, toWire(document.root, limits), 0, limits));},
    pack(document) {const limits = check(document); return call(2, toWire(document.root, limits), 0, limits);},
    unpack(buffer, offset = 0, options = {}) {
      if (!(buffer instanceof Uint8Array) || !Number.isSafeInteger(offset) || offset < 0 || offset > buffer.length) throw new TypeError('Expected Uint8Array and valid offset');
      const limits = limitsOf(options.limits); return restored(call(3, buffer, offset, limits), limits);
    },
    validate(document, options = {}) {
      client.dumps(document); const features = new Set(options.features ?? []);
      for (const feature of document.metadata.requires ?? []) if (!features.has(feature)) throw new YLSpecError('Unsupported required feature: ' + feature, 'unsupported');
      const {profile, profile_version: revision} = document.metadata;
      if (profile === 'core.data' && revision === '0.1') return document;
      const validator = options.validators?.get(profile + '@' + revision);
      if (!validator) throw new YLSpecError('Unsupported profile: ' + profile + '@' + revision, 'unsupported');
      if (validator(document) === false) throw new YLSpecError('Profile rejected document', 'profile'); return document;
    },
    async readAt(reader, offset, available, options = {}) {
      if (typeof offset !== 'bigint' || typeof available !== 'bigint' || offset < 0n || available < 32n || offset + available > (1n << 64n) - 1n) throw new RangeError('Invalid frame region');
      const limits = limitsOf(options.limits); const header = await reader(offset, 32);
      if (!(header instanceof Uint8Array) || header.length !== 32) throw new YLSpecError('Short header read', 'io');
      const view = new DataView(header.buffer, header.byteOffset, 32);
      const magic = [89, 76, 83, 80, 69, 67, 0, 0];
      if (!magic.every((v, i) => header[i] === v)) throw new YLSpecError('Invalid YLSpec magic', 'frame');
      if (view.getUint16(8, true) !== 0 || view.getUint16(10, true) !== 1 || view.getUint32(12, true) !== 32 || view.getUint32(24, true) !== 1 || view.getUint32(28, true) !== 0) throw new YLSpecError('Unsupported frame header', 'unsupported');
      const size = view.getBigUint64(16, true);
      if (size > BigInt(limits.maxDocumentBytes)) throw new YLSpecError('Embedded document limit exceeded', 'limit');
      if (size > available - 32n) throw new YLSpecError('Truncated frame region', 'frame');
      const payload = await reader(offset + 32n, Number(size));
      if (!(payload instanceof Uint8Array) || payload.length !== Number(size)) throw new YLSpecError('Short payload read', 'io');
      const frame = new Uint8Array(32 + Number(size)); frame.set(header); frame.set(payload, 32); return client.unpack(frame, 0, {limits});
    },
  };
  return Object.freeze(client);
}
