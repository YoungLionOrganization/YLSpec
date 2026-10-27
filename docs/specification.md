# YLSpec 0.1 specification

**Status:** experimental. **Normative language:** English.
The keywords MUST, MUST NOT, SHOULD, and MAY describe requirements for an
implementation claiming YLSpec 0.1 compatibility. Examples are informative.

## Document model

A standalone document MUST be a well-formed UTF-8 TOML 1.1 document. Literal NUL
bytes and a leading byte-order mark are invalid. Newlines may be LF or CRLF.
TOML's strings, signed integers, floats, booleans, temporal values, arrays, and
tables retain their TOML meanings. Null is not a TOML value.

The root MUST contain `_ylspec` and `data` tables. It MAY also contain an
`extensions` table. Other root fields MUST be rejected in version 0.1.

| `_ylspec` field | Type | Requirement |
|---|---|---|
| `version` | String | Exactly `0.1` |
| `profile` | Nonempty string without NUL | Required |
| `profile_version` | Nonempty string without NUL | Required |
| `requires` | Array of nonempty strings without NUL | Optional; default empty |

Other `_ylspec` fields MUST be rejected. This restriction prevents silent
reinterpretation of a future standard field. `data` MAY contain any TOML table
structure supported within the implementation's documented resource limits.

Every direct entry in `extensions` MUST be a table with a nonempty namespace key
without NUL. Reverse-domain namespaces such as `xyz.younglion.desktop` are
recommended; they are quoted as one TOML key. Namespace assignment is not a
network lookup, ownership certificate, or centrally hosted registry.

## Profiles and required features

`core.data` at profile version `0.1` imposes no constraints beyond this envelope.
It is suitable for application-defined configuration, manifests, and general
data. A profile defines meaning and validation, not a different text grammar.

An implementation MUST distinguish structural parsing from profile validation.
Unknown profile documents MAY be parsed and inspected as inert data. Validation
MUST fail with an unsupported status when the profile or its version is unknown,
or when a named required feature is not supported. Applications MUST explicitly
validate before relying on profile-specific meaning.

Optional extensions MUST be preserved by semantic round trips. They MUST NOT
override reserved envelope fields. `requires` names capabilities needed to use
the document, including any extension whose omission would change its meaning.
Applications register their support explicitly; loading an extension is never
implicit.

## Embedding frame

The binary frame MUST contain the following header immediately followed by the
declared number of UTF-8 document bytes. All integer fields are unsigned and
little-endian. No native-ABI struct layout or padding is part of the format.

| Offset | Bytes | Field | Required value |
|---:|---:|---|---|
| 0 | 8 | Magic | `59 4c 53 50 45 43 00 00` |
| 8 | 2 | Frame major | 0 |
| 10 | 2 | Frame minor | 1 |
| 12 | 4 | Header bytes | 32 |
| 16 | 8 | Document bytes | Length of the following text |
| 24 | 4 | Encoding | 1: UTF-8/TOML 1.1 |
| 28 | 4 | Flags | 0 |

Unknown versions, header lengths, encodings, or nonzero flags MUST be rejected
by the 0.1 decoder. Byte limits and the host region's bounds MUST be checked
before allocating payload memory. Offset and length addition MUST be checked
for overflow. Zero-byte text is not a valid YLSpec document.

Trailing host bytes are permitted and are outside this frame. The consumed
length is exactly `32 + document_bytes`. The frame requires no alignment. Hosts
MAY store multiple frames and MUST define how each frame's location is found.
Magic scanning alone MUST NOT be treated as authoritative discovery.

## Serialization and errors

Serialization MUST preserve value meaning and exact temporal precision. It need
not preserve comments, whitespace, quote choices, table order, or integer radix.
NaN remains a float NaN; its payload bits and sign are not significant.

The reference serializer uses quoted keys and inline table/array forms to avoid
ambiguous dotted-key reconstruction. Its output is deterministic for an
unchanged tree and insertion order, but is not a cryptographic canonicalization
format. A host signing content should sign the actual stored bytes.

Errors MUST be distinguishable for invalid structure, text syntax, resource
limits, allocation failure, invalid framing, unsupported capabilities, I/O, and
profile rejection. Diagnostic positions use zero-based byte offsets and
one-based line/column numbers where available. Zero line/column means unknown.

## Boundaries and conformance

A conforming parser MUST NOT execute commands, perform network access, expand
environment variables, resolve includes, or load host payload code.
Authentication, compression of unrelated host payloads, and payload indexing
belong to the host format.

Published implementation limits are permitted. The reference defaults and
parser ceilings are in [compatibility](compatibility.md). The normative contract
and test vectors take precedence over undocumented reference behavior. Changes
go through [the contribution process](../CONTRIBUTING.md); experimental version
0.x does not claim approval by ISO, IETF, or another standards body.
