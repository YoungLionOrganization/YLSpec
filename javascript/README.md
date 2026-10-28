# YLSpec for JavaScript and TypeScript

Copyright 2026 Cavanşir Qurbanzadə. Apache-2.0.

The Node.js backend is a C Node-API addon. Browsers and React applications use
WebAssembly compiled from the same C parser. There is no independent JavaScript
TOML parser and no runtime npm dependency. The package includes TypeScript types.

```sh
npm install @younglionorganization/ylspec
```

This command requires a completed npm publication. Before then, install the
checksummed `younglionorganization-ylspec-0.1.1.tgz` asset from the GitHub Release
with `npm install ./younglionorganization-ylspec-0.1.1.tgz`. Installation never
downloads or compiles a native binary; supported binaries are already packaged.

## Node.js and TypeScript

```js
import {createClient} from '@younglionorganization/ylspec';
const yl = await createClient();
const doc = new yl.Document({name: 'Example', count: 42n});
const restored = yl.unpack(yl.pack(doc));
console.log(restored.data.count); // 42n
```

CommonJS uses `const {createClient} = require('@younglionorganization/ylspec')`
and the same async factory. Node ESM consumers needing synchronous initialization
can use the default client from `@younglionorganization/ylspec/node`.

```typescript
import {createClient, type Document, type Reader} from '@younglionorganization/ylspec';
const yl = await createClient();
const document: Document = yl.loads(`
[_ylspec]
version = "0.1"
profile = "core.data"
profile_version = "0.1"
[data]
name = "Typed consumer"
count = 9223372036854775807
`);
const frame = yl.pack(document);
const reader: Reader = (offset, count) => frame.slice(Number(offset), Number(offset) + count);
const restored = await yl.readAt(reader, 0n, BigInt(frame.length));
console.assert(restored.data.count === 9223372036854775807n);
```

The declaration files cover factory options, document data, exact temporal
values, resource limits, profile validators, errors, and callback reads. Both
ESM and CommonJS resolution are exercised with TypeScript's NodeNext mode.

## Browser and React

The package's browser export condition selects WebAssembly. An explicit
`@younglionorganization/ylspec/web` import is also available. In React initialize
the client in an effect or application-level resource, retain it across renders,
and handle cancellation/errors. For SSR initialize the browser client on the
client side. Bundlers must serve the accompanying `wasm/core.wasm` asset; a
`wasmBinary: Uint8Array` factory option supports custom asset delivery and CSP.

For custom bundlers, explicitly fetch the emitted WebAssembly asset and pass
its bytes to the factory. The deployment must permit WebAssembly compilation
under its content security policy. Do not move parsing into a React render.

```tsx
import {useEffect, useState} from 'react';
import {createClient} from '@younglionorganization/ylspec/web';

export function ComponentMetadata() {
  const [name, setName] = useState('Loading');
  useEffect(() => {
    let active = true;
    void createClient().then(yl => {
      const document = new yl.Document({name: 'Example component'});
      const restored = yl.unpack(yl.pack(document));
      if (active) setName(String(restored.data.name));
    }).catch(() => {
      if (active) setName('Unable to load metadata');
    });
    return () => {active = false;};
  }, []);
  return <output aria-live="polite">{name}</output>;
}
```

For frequently used clients, cache the initialization promise at application
scope. Each factory owns an independent WebAssembly instance. The package does
not depend on React; other browser frameworks use the same factory. React SSR
applications should initialize the browser adapter in client-side code.

## Types and validation

| Value | Representation |
|---|---|
| TOML integer | JavaScript bigint, preserving all signed 64-bit values |
| TOML float | JavaScript number; number inputs always encode as floats |
| Exact date/time | `new yl.TemporalValue(kind, text)` |
| JavaScript Date input | UTC offset datetime; the Date's existing precision applies |
| Table | Plain object; decoded objects have null prototypes |
| Array | Array of supported values |
| null, undefined, functions, cycles | Rejected |

`yl.loads`, `yl.dumps`, `yl.pack`, `yl.unpack`, and `yl.validate` operate
synchronously after initialization. `yl.readAt(reader, offset, available)` is
asynchronous and uses bigint host offsets. Its callback receives an absolute
offset and exact byte count; only the frame header and its document are read.
The host owns file discovery, stream ownership, and synchronization.

Default limits are 16 MiB and depth 64. Optional limits use `maxDocumentBytes`
and `maxDepth`. Profile validators use Map keys `profile@revision`; unsupported
profiles or required features fail explicitly. Errors from C expose `code`,
`offset`, `line`, and `column`. No frame authenticates content or executes code.

Native binaries are packaged by platform and architecture. Unsupported native
hosts fail with a diagnostic; applications can explicitly choose WebAssembly.
Build instructions and registry setup are in the repository's language guides.

## API overview

| Operation | Result | Notes |
|---|---|---|
| `new yl.Document(data, options?)` | Document | Generic profile by default; mutable `root`, `data`, and `extensions` |
| `yl.loads(text, options?)` | Document | Length-bounded C parse; does not implicitly approve custom profiles |
| `yl.dumps(document)` | String | Semantic serialization; comments and whitespace are not preserved |
| `yl.pack(document)` | Uint8Array | Standard 32-byte frame and UTF-8 document |
| `yl.unpack(bytes, offset?, options?)` | Document | Explicit byte offset; no scanning |
| `yl.validate(document, options?)` | The supplied Document | Checks required capabilities and an explicit profile validator |
| `yl.readAt(reader, offset, available, options?)` | Promise of Document | Two exact reads; uint64 host offsets represented by bigint |

`new yl.TemporalValue('datetime-offset', '2026-10-29T12:00:00.123456789Z')`
preserves all written fractional digits. A regular JavaScript Date input carries
only the precision already present in that Date.

### Profiles and limits

```javascript
const yl = await createClient();
const document = new yl.Document({name: 'Component'}, {
  profile: 'xyz.example.component',
  profileVersion: '1',
  limits: {maxDocumentBytes: 1024 * 1024, maxDepth: 32}
});
yl.validate(document, {
  validators: new Map([['xyz.example.component@1', doc => typeof doc.data.name === 'string']])
});
```

Validators run only during explicit validation. Return `false` to reject a
document, or throw an application error. Supported feature identifiers are
passed through the `features` iterable; a mandatory feature outside that set
is an `unsupported` error. Unknown profiles remain parseable and inspectable.

### Embedded reads and errors

The host supplies `offset` and `available` as nonnegative bigint values within
the uint64 range. The callback receives `(absoluteOffset, exactByteCount)` and
returns a Uint8Array or a promise for it. A short header or payload is an `io`
error. Magic, version, encoding, flags, declared length, and limits are checked
before requesting the payload. Unrelated host bytes are not requested.

`YLSpecError` includes `code`, `offset`, `line`, and `column`. Source coordinates
are supplied where the C parser can locate the error; zero means unavailable.
JavaScript input-shape violations may instead raise TypeError or RangeError.
Treat framing as a boundary and encoding contract; authenticity belongs to
the host format.

## Distribution and verification

The npm tarball contains seven desktop Node-API targets and one browser
WebAssembly build. Linux GNU targets use manylinux 2.28; musl builds are separate.
macOS targets use a minimum deployment version of 11.0. Windows x64 is supported;
Windows ARM64 and 32-bit desktop targets are outside the initial matrix.

GitHub verification executes native consumers on every target, tests signed
64-bit values and temporal precision, checks exact callback read boundaries and
truncated frames, type-checks public ESM/CommonJS imports, and launches React in
Chromium against the compiled C WebAssembly. The release tarball is installed
into a clean consumer directory before release assembly.

See [registry account setup](../docs/registries.md),
[compatibility](../docs/compatibility.md), and [the standard](../docs/specification.md).
Original code is Apache-2.0; bundled tomlc17 retains its MIT license and notices.
