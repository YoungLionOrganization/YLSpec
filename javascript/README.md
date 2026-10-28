# YLSpec for JavaScript and TypeScript

Copyright 2026 Cavanşir Qurbanzadə. Apache-2.0.

The Node.js backend is a C Node-API addon. Browsers and React applications use
WebAssembly compiled from the same C parser. There is no independent JavaScript
TOML parser and no runtime npm dependency. The package includes TypeScript types.

```sh
npm install @younglionorganization/ylspec
```

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

The package's browser export condition selects WebAssembly. An explicit
`@younglionorganization/ylspec/web` import is also available. In React initialize
the client in an effect or application-level resource, retain it across renders,
and handle cancellation/errors. For SSR initialize the browser client on the
client side. Bundlers must serve the accompanying `wasm/core.wasm` asset; a
`wasmBinary: Uint8Array` factory option supports custom asset delivery and CSP.

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
