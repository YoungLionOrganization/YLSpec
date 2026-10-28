# Compatibility and migration policy

## Independent version boundaries

| Version | Initial value | Meaning |
|---|---|---|
| Library release | `0.1.1` | C core, language adapters, and tools |
| Document format | `0.1` | Envelope and document semantics |
| Embedding frame | major 0, minor 1 | Binary framing contract |
| Generic profile | `core.data` / `0.1` | Unconstrained data-table profile |
| Host/application version | Host-defined | Outside this specification |

Do not infer one version from another. An application field named `version`
does not change the YLSpec document version.

## Platform targets

| Platform | Native packages | Python wheels |
|---|---|---|
| Windows x64 | Static/shared C and CLI | CPython `abi3`, AMD64 |
| Linux x86_64 | Static/shared C and CLI | manylinux 2.28+, musllinux 1.2+ |
| Linux ARM64 | Static/shared C and CLI | manylinux 2.28+, musllinux 1.2+ |
| macOS Intel | Static/shared C and CLI | macOS 11+, x86_64 |
| macOS Apple Silicon | Static/shared C and CLI | macOS 11+, arm64 |

The native Linux archives use the GitHub Ubuntu 24.04 toolchain; they do not
claim the older glibc baseline of manylinux wheels. ARM wheels run on native ARM
GitHub runners. Standard CPython 3.11–3.15 is tested; PyPy, free-threaded Python,
Windows ARM64/32-bit are outside the initial desktop targets. Android JNI and
browser WebAssembly have separate adapters and verification; they are not
Python wheel targets.

## Additional language targets

| Adapter | Targets and baseline |
|---|---|
| Node-API | Node.js 20+; Linux x64/ARM64 GNU and musl, Windows x64, macOS x64/ARM64 |
| Node GNU binaries | Built on manylinux 2.28 images; separate from Ubuntu-built C archives |
| Browser WebAssembly | Modern browsers with WebAssembly, TextEncoder/TextDecoder, and BigInt; Chromium/React exercised in CI |
| JVM JNI | Java 8 bytecode; JDK 17 executes Java and Kotlin verification |
| Android JNI | API 26+; armeabi-v7a, arm64-v8a, x86, x86_64; x86_64 emulator runtime verification |
| VS Code | Desktop or remote Node-enabled extension host, VS Code 1.95+; bundled WebAssembly |

The npm package has no runtime npm dependencies or install-time binary downloads.
The JVM desktop loader extracts a packaged JNI resource; Android loads the
separately compiled AAR library. Browser and editor adapters package the C core
as WebAssembly. Their common internal value transport is an implementation
detail, not a new public file format or host-container specification.

### Language type mapping

| TOML / YLSpec | Python | JavaScript / TypeScript | Java / Kotlin |
|---|---|---|---|
| Integer | `int` within signed 64-bit range | `bigint`; `number` inputs are floats | `Long`; smaller integer input wrappers accepted |
| Float | `float` | `number` | `Double`; Float input accepted |
| Boolean | `bool` | `boolean` | `Boolean` |
| String | `str` | `string` | `String` |
| Array | `list` | Array | List |
| Table | `dict` | Own properties on a plain or null-prototype object | String-key Map |
| Temporal | `TemporalValue(kind, text)` | `TemporalValue(kind, text)` | `TemporalValue(kind, text)` |

Standard date/time objects may be accepted as inputs; no adapter silently lowers
the precision of a parsed temporal literal. Null values and cyclic containers
are not TOML values. Serialization preserves value meaning and may change
spelling, comments, whitespace, and layout.

## Resource and parser limits

Defaults: 16 MiB UTF-8 source and depth 64. The configurable depth ceiling is
128. Root depth is zero; every table/array child edge increments depth, including
the envelope's `data` table. Document bytes cannot exceed `INT_MAX` because the
vendored parser's input length is an `int`.

Additional vendored-parser ceilings are 16,384 entries per table or array,
129 components in a dotted key, bounded literal buffers, and bracket/brace
recursion ceilings of 128 each. Deeply nested structures can hit the aggregate
document depth limit before a parser ceiling. Malformed input must fail rather
than silently truncate. Very long numeric/temporal tokens may be rejected even
when source byte limits would otherwise permit them.

Strings and data keys support escaped NUL. Source files cannot contain literal
NUL. Ints are signed 64-bit; floats are binary64. Temporal literals preserve
their input precision, subject to the parser's literal-size ceiling.

## Experimental releases and migration

Version 0.x APIs and format revisions may change. Each breaking change must
include a new documented version boundary, release notes, and a migration
example. Existing readers reject unsupported document/frame versions; they do
not guess a compatible interpretation. During 0.x, rebuild native consumers
when changing library releases.

A stable 1.0 will require a reviewed frozen specification, published conformance
vectors, and agreement between independent implementations. The Python binding
shares the C core and is not counted as an independent parser implementation.
