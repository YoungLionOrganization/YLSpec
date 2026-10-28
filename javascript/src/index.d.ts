/** Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
 * Native-backed YLSpec contract shared by Node-API and browser WebAssembly.
 * The factory is asynchronous; operations on an initialized client are synchronous
 * except readAt. All integers decode to bigint, preserving the entire int64 range.
 * JavaScript number inputs encode as TOML floats, including integral numbers.
 */
export type TemporalKind = 'date' | 'time' | 'datetime' | 'datetime-offset';
export type Value = string | boolean | number | bigint | Date | TemporalValue | Value[] | Table;
export interface Table { [key: string]: Value; }
export interface Limits { maxDocumentBytes?: number; maxDepth?: number; }
export interface Metadata { version: '0.1'; profile: string; profile_version: string; requires?: string[]; }
export interface Root { _ylspec: Metadata; data: Table; extensions?: Record<string, Table>; }
/** Exact temporal text. No conversion to a millisecond-resolution Date is implicit. */
export interface TemporalValue { readonly kind: TemporalKind; readonly text: string; }
export interface Document { root: Root; limits: Required<Limits>; readonly data: Table; readonly metadata: Metadata; readonly extensions: Record<string, Table>; }
export interface DocumentOptions { profile?: string; profileVersion?: string; extensions?: Record<string, Table>; limits?: Limits; }
export interface ParseOptions { limits?: Limits; }
export interface ValidateOptions { features?: Iterable<string>; validators?: ReadonlyMap<string, (document: Document) => unknown>; }
export interface YLSpecError extends Error { code: string; offset: number; line: number; column: number; }
/** Read exactly size bytes from an absolute uint64 offset. Hosts own discovery. */
export type Reader = (offset: bigint, size: number) => Uint8Array | Promise<Uint8Array>;
export interface Client {
  readonly backend: 'node-api' | 'wasm';
  readonly version: string;
  readonly Document: new (data?: Table, options?: DocumentOptions) => Document;
  readonly TemporalValue: new (kind: TemporalKind, text: string) => TemporalValue;
  readonly YLSpecError: new (message: string, code?: string, position?: {offset?: number; line?: number; column?: number}) => YLSpecError;
  /** Parse text without implicitly approving a custom profile or required feature. */
  loads(text: string, options?: ParseOptions): Document;
  /** Serialize through C; comments and spacing are not retained. */
  dumps(document: Document): string;
  /** Produce the standard 32-byte frame plus uncompressed UTF-8 text. */
  pack(document: Document): Uint8Array;
  /** Decode at an explicit offset; no magic scanning or host-payload loading. */
  unpack(buffer: Uint8Array, offset?: number, options?: ParseOptions): Document;
  /** Validate capabilities and profile. Validator map keys are profile@revision. */
  validate<D extends Document>(document: D, options?: ValidateOptions): D;
  /** Two bounded reads, with length/header checks before requesting the payload. */
  readAt(reader: Reader, offset: bigint, available: bigint, options?: ParseOptions): Promise<Document>;
}
export interface ClientOptions { wasmBinary?: Uint8Array; }
/** Node uses the native addon; the browser export condition selects WebAssembly. */
export function createClient(options?: ClientOptions): Promise<Client>;
