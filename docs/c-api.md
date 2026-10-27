# C API and ownership

Include `ylspec.h` and link `YLSpec::ylspec`. All public functions have C linkage
when included from C++. The core requires a hosted C11 environment and the
standard allocator; it does not depend on Python or OS-specific file APIs.

## Main operations

| Operation | Functions |
|---|---|
| Version and limits | `yl_version`, `yl_default_limits` |
| Parse/create | `yl_parse`, `yl_document_create` |
| Inspect/mutate root | `yl_root`, `yl_root_mutable` |
| Construct values | `yl_new`, `yl_string`, `yl_integer`, `yl_float`, `yl_boolean`, `yl_temporal` |
| Read values | `yl_value_type`, `yl_value_text`, numeric getters, `yl_temporal_kind` |
| Tables/arrays | `yl_get`, `yl_key`, `yl_at`, `yl_count`, `yl_set`, `yl_append` |
| Serialize/frame | `yl_dump`, `yl_pack`, `yl_unpack`, `yl_read_at` |
| Validate profiles | `yl_validate` with a caller-owned `yl_registry` |
| Release memory | `yl_document_free`, `yl_value_free`, `yl_buffer_free` |

Use `yl_new(YL_TABLE)` or `yl_new(YL_ARRAY)` for containers. Prefer typed
constructors for scalars. Text/key sizes are in bytes and may include embedded
NUL in application strings and data keys. Reserved envelope identifiers and
extension namespace keys cannot contain NUL. Always check a value's type before
using a scalar getter; getters do not perform implicit conversion.

## Ownership rules

- Constructors return an unowned heap value or NULL.
- A successful `yl_set` or `yl_append` transfers ownership to the container.
  A failed insertion leaves the new value owned by the caller.
- Replacing an existing table key frees its previous value and invalidates
  references into that subtree. A value can have only one parent. Cycles and
  trees beyond the hard depth ceiling are rejected.
- Successful `yl_document_create` transfers the root to the document; failure
  leaves it with the caller. Parsing creates an independently owned tree.
- Accessors return borrowed pointers. They remain valid until their owning
  subtree is replaced or the document is freed.
- Free only unowned roots with `yl_value_free`. Calling it on an attached child
  is ignored; free its owning document instead.
- Output buffers are owned by the caller and released with `yl_buffer_free`.
  Text dumps contain a convenience terminating NUL excluded from `size`; binary
  frames are not strings.

Destroy documents with `yl_document_free`, not `free`. Do not copy opaque
document/value internals or allocate them on the stack.

## Mutation and serialization

Build or mutate the typed tree with insertion functions, then call `yl_dump` or
`yl_pack`. These revalidate structure and configured depth. Serializing an
invalid edited envelope fails rather than emitting an invalid document. Call
`yl_validate` separately for domain constraints and required-feature handling.

Temporal constructors use `date`, `time`, `datetime`, or `datetime-offset` and
an exact valid TOML literal. They reject comment or newline injection. The source
literal is retained, including fractional-second digits beyond microseconds.

## Errors and limits

Functions return `yl_status`. Passing a non-NULL `yl_error` receives a code,
message, payload-relative byte offset, and line/column when known. Outputs are
initialized to empty on failure. Syntax diagnostics inherited from the parser
have the correct line and a conservative column of 1; they do not claim an exact
token column. Other diagnostics may have zero position fields.

Use `yl_limits` to adjust document byte and depth limits. Root depth is zero.
The configurable maximum depth is 128; parser-specific ceilings still apply.
No stable binary ABI is promised during 0.x. Rebuild consumers when upgrading.

## Concurrency and callbacks

Independent documents may be used in different threads. A shared mutable
document or stream requires external synchronization. YLSpec does not change
process-global parser options or locale. Do not mutate the vendored parser's
global settings from application code.

Callbacks run synchronously. Keep registry entries, feature names, and callback
contexts alive for the duration of validation or reading. Registries belong to
the caller; there is no global registry or runtime module loading.

See [profiles](profiles.md), [embedding](embedding.md), and the
[public header](../include/ylspec.h) for the complete signatures.
