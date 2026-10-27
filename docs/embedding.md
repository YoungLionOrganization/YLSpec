# Embedding YLSpec in a host format

The host owns the file layout. YLSpec owns one bounded metadata block.
This separation allows a game asset, database record, executable section, or
future package to use the same metadata reader without sharing a container
design.

```text
Offset supplied by host ──────┐
                             ▼
┌───────────────┬───────────────┬───────────────────┬──────────────────┐
│ Host prefix   │ 32-byte      │ Document text     │ Unrelated bytes  │
│               │ frame header│ document_bytes    │                  │
└───────────────┴───────────────┴───────────────────┴──────────────────┘
                └──────── available region ───────┘
```

## Host integration contract

1. Store a frame produced by `yl_pack` or `ylspec.pack`.
2. Record its offset and an enclosing region length in the host's own header,
   section table, record schema, or other authoritative locator.
3. Pass that offset and available length to the YLSpec reader.
4. Explicitly validate the document's profile and required features before
   relying on its domain-specific meaning.
5. Verify any host signature or integrity policy separately.

The available region may include subsequent host bytes. A successful read still
consumes exactly the frame's header and payload, and returns the consumed length
through the C API. For the tightest boundary, pass the recorded frame length.
Python's `read_at` can determine available bytes by seeking to EOF if omitted.

## C callback

`yl_read_at_fn(context, absolute_offset, buffer, size)` must fill exactly `size`
bytes and return zero. Short reads, inaccessible regions, or failed seeks return
nonzero. YLSpec first requests 32 bytes, validates them, then requests the exact
document size. A valid frame causes two reads. No decompression, whole-file
buffering, alignment, or signature scan is needed.

The core uses `uint64_t` offsets so a small document may live beyond the 4 GiB
boundary. The adapter is responsible for supporting the host's address space.
The reference CLI uses 64-bit seek APIs.

## Python example

```python
import io
import ylspec

first = ylspec.pack(ylspec.Document({"name": "first"}))
second = ylspec.pack(ylspec.Document({"name": "second"}))
host = io.BytesIO(b"prefix!" + first + second + b"payload")
metadata = ylspec.read_at(host, offset=7 + len(first), available=len(second))
assert metadata.data["name"] == "second"
```

`read_at` restores the initial stream position, including on errors. Shared
streams need external synchronization because seeking changes stream state.
`unpack` accepts an already available bytes buffer; it does not discover frames.

## Integrity and evolution

Frame length fields prevent out-of-region reads; they do not prove who wrote
the data. The initial frame contains no checksum, signature, compression codec,
or application payload. A host can authenticate the whole record or store hashes
in its own authenticated structures.

Keep the document version, frame version, profile version, application version,
and host-format version distinct. A future frame revision must not be disguised
as a currently supported encoding or hidden behind nonzero flags.
