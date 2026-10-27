# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Low-level type contract for the CPython extension over the YLSpec C core.

These functions are implementation details. Applications should normally use
the public Document API, which translates native errors and temporal values.
All native call arguments are positional-only because the extension methods
use METH_VARARGS rather than keyword-aware argument parsing.

Native tables are ordinary string-keyed dictionaries. Temporal scalar values
are represented by a two-element tuple containing a kind and literal UTF-8
bytes. That tuple is distinct from an application array, represented as a list.
The public wrapper converts it to/from TemporalValue instances.

Structured core failures are raised as ValueError with six arguments:
numeric status, symbolic status, payload-relative offset, line, column, and
message. The wrapper translates that transport convention to typed exceptions.
Argument conversion can also raise TypeError, OverflowError, or MemoryError.
"""

from collections.abc import Callable as _Callable
from typing import Literal as _Literal, TypeAlias as _TypeAlias

__version__: str
"""Version of the C implementation linked into this extension."""

_TemporalKind: _TypeAlias = _Literal["date", "time", "datetime", "datetime-offset"]
_Temporal: _TypeAlias = tuple[_TemporalKind, bytes]
_Value: _TypeAlias = str | int | float | bool | _Temporal | list["_Value"] | dict[str, "_Value"]
_Table: _TypeAlias = dict[str, _Value]
_Reader: _TypeAlias = _Callable[[int, int], bytes]

def decode(text: bytes, max_document_bytes: int, max_depth: int, /) -> _Table:
    """Parse an explicitly sized standalone document and return its native tree.

    text must be a bytes object accepted by the extension's read-only bytes
    parser; it is not interpreted as a path. The C core checks UTF-8, limits,
    TOML syntax, and the standard envelope. max_depth must be positive and at
    most 128. The default policy is supplied by the public wrapper, not here.

    Native document ownership ends before this function returns. Returned
    dictionaries, lists, strings, and temporal tuples are owned Python values,
    not borrowed pointers into released C memory.
    """
    ...

def encode(
    root: _Table,
    max_document_bytes: int,
    max_depth: int,
    framed: bool,
    /,
) -> bytes:
    """Construct a C tree from normalized Python values and serialize it.

    root must contain the complete envelope, not only application data. String
    keys, signed 64-bit integers, booleans, binary64 floats, temporal transport
    tuples, lists, and dictionaries are supported. The public wrapper normalizes
    other accepted mappings, tuples, and datetime inputs before this call.

    With framed=False, returns UTF-8 document bytes. With framed=True, returns
    the 32-byte embedding header followed by the same serialized text. Byte
    limits apply to text; the header is additional. Structural validation does
    not approve an application profile or authenticate metadata.

    Ownership of Python inputs is retained by the caller. Temporary native
    trees and output buffers are released before returning or raising.
    """
    ...

def unpack(
    buffer: bytes,
    offset: int,
    max_document_bytes: int,
    max_depth: int,
    /,
) -> tuple[_Table, int]:
    """Decode one frame and return its root plus the consumed frame byte count.

    offset is relative to the start of buffer. On success the consumed length
    is 32 plus the header's document length; it excludes prefix/trailing host
    content. Header bounds, integer overflow, supported revision/encoding/flags,
    and configured text limits are checked before document parsing.

    The public unpack wrapper exposes only Document. Low-level users must not
    mistake the returned frame length for an absolute end offset.
    """
    ...

def read_at(
    reader: _Reader,
    offset: int,
    available: int,
    max_document_bytes: int,
    max_depth: int,
    /,
) -> _Table:
    """Decode a bounded frame using an absolute-offset read callback.

    reader(position, size) must return exactly size bytes or raise. A valid
    frame requests the header first and its text payload second. available is
    the size of the host-defined region starting at offset, not the host's
    absolute end position. Both offset and available use unsigned 64-bit bounds.

    Callback exceptions propagate. A callback returning a different byte count
    or a non-bytes result raises OSError. The callback runs synchronously with
    the GIL held; the native function neither closes a stream nor restores its
    position. The public wrapper supplies that stream management separately.
    """
    ...
