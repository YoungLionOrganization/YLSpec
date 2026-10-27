# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Typed public interface to YLSpec's native-backed document API.

This file accompanies the implementation and the PEP 561 ``py.typed`` marker.
Editors and static analyzers use these signatures without importing the native
extension. Installing ``ylspec`` is sufficient; a separate stub package is not
required. The interface targets Python 3.11 and newer.

A document contains a reserved metadata envelope, an application data table,
and optional namespaced extension tables. Reading checks syntax and envelope
structure; application-specific profile approval is an explicit ``validate``
operation. Serialization never executes application code embedded in data.

Recursive value types describe values accepted when constructing or editing a
document. Parsed temporal values use ``TemporalValue``; Python date/time objects
are accepted as serialization inputs. TOML has no null or raw-bytes value.
"""

from collections.abc import Callable as _Callable, Iterable as _Iterable, Mapping as _Mapping
from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime, time as _time
from os import PathLike as _PathLike
from typing import Literal as _Literal, NotRequired as _NotRequired, Protocol as _Protocol
from typing import Self as _Self, TypeAlias as _TypeAlias, TypedDict as _TypedDict

__all__ = [
    "Document", "TemporalValue", "Limits", "Error", "ParseError", "LimitError",
    "FrameError", "UnsupportedError", "ProfileError", "loads", "dumps", "load",
    "dump", "pack", "unpack", "read_at", "__version__",
]

__version__: str
"""Implementation release version, distinct from format and profile versions."""

_TemporalKind: _TypeAlias = _Literal["date", "time", "datetime", "datetime-offset"]

class Error(ValueError):
    """Base exception for structured errors originating from the document core.

    ``code`` is the symbolic C-core status, such as ``syntax`` or ``unsupported``.
    ``offset`` is a zero-based byte position within the document payload, not an
    absolute position in its host file. ``line`` and ``column`` are one-based
    when available; zero denotes an unavailable position. Syntax errors inherited
    from the parser may conservatively identify the beginning of a source line.

    Ordinary argument errors, integer overflow, Python allocations, and file
    operations may instead raise standard Python exceptions. Catching this base
    class does not catch all possible ``OSError`` or ``MemoryError`` instances.
    """

    code: str
    """Symbolic status: invalid, syntax, limit, memory, frame, unsupported, io, or profile."""
    offset: int
    """Payload-relative byte offset; zero may also mean no precise offset is available."""
    line: int
    """One-based source line, or zero for a non-source or unavailable location."""
    column: int
    """One-based source column, or zero; parser errors can conservatively use column one."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid",
        offset: int = 0,
        line: int = 0,
        column: int = 0,
    ) -> None:
        """Initialize a message and optional structured diagnostic information.

        Applications may construct errors in their own validators. The fields
        are mutable instance attributes, and ``str(error)`` returns the message.
        No file path, host identity, or authentication state is inferred.
        """
        ...

class ParseError(Error):
    """Invalid TOML text, malformed UTF-8, or another source-syntax failure.

    Inspect ``line``, ``column``, and ``offset`` when reporting source problems.
    Parsing can also raise ``UnsupportedError`` for a well-formed document using
    an unsupported format version, or ``Error`` for an invalid envelope.
    """
    ...

class LimitError(Error):
    """A configured source-size or value-depth limit was exceeded.

    Raising a source-size limit does not remove the parser's documented hard
    ceilings. Cyclic Python input is rejected by the construction depth guard.
    """
    ...

class FrameError(Error):
    """An embedding frame is malformed, truncated, or outside its supplied region.

    An unsupported frame revision, encoding, header length, or flag is reported
    as ``UnsupportedError``. A short read from a Python stream raises ``OSError``.
    """
    ...

class UnsupportedError(Error):
    """A format, encoding, profile, profile revision, or required feature is unsupported.

    Unknown application profiles remain parseable as inert metadata. Calling
    ``Document.validate`` without the matching validator rejects them explicitly.
    """
    ...

class ProfileError(Error):
    """An application-specific profile validator rejected a document.

    Returning the exact singleton ``False`` from a Python validator produces
    this error. An exception raised by a validator propagates unchanged.
    """
    ...

@_dataclass(frozen=True)
class Limits:
    """Immutable resource limits for a document and its subsequent serialization.

    The defaults are 16 MiB of UTF-8 source and 64 value-tree edges from the root.
    Envelope tables count toward that depth. Maximum configurable depth is 128;
    additional parser ceilings remain in force. Limits bound the serialized
    document, not the complete size of a host file or every heap allocation.
    """

    max_document_bytes: int = 16_777_216
    """Positive maximum payload byte count; the 32-byte frame header is excluded."""
    max_depth: int = 64
    """Maximum depth, in the inclusive range 1 through 128; root depth is zero."""

    def __post_init__(self) -> None:
        """Reject invalid limits with ValueError after dataclass initialization.

        The Python wrapper accepts a positive byte limit up to ``2**63 - 1``;
        the native parser additionally rejects source lengths above INT_MAX.
        """
        ...

@_dataclass(frozen=True)
class TemporalValue:
    """An exact TOML temporal literal, including every fractional-second digit.

    ``date`` represents a local date, ``time`` a local time, ``datetime`` a local
    datetime, and ``datetime-offset`` an offset datetime. The text is retained
    rather than implicitly converted to Python's microsecond-resolution types.

    Construction stores the fields without parsing. The native serializer
    validates the kind/literal combination when the containing document is
    serialized. Arbitrary comments, newlines, and invalid temporal values are
    rejected instead of being inserted into generated TOML.
    """

    kind: _TemporalKind
    """One of date, time, datetime, or datetime-offset."""
    text: str
    """Exact TOML temporal token, such as 2026-10-27T12:34:56.123456789Z."""

_Scalar: _TypeAlias = str | int | float | bool | TemporalValue | _date | _time | _datetime
_Value: _TypeAlias = _Scalar | _Mapping[str, "_Value"] | list["_Value"] | tuple["_Value", ...]
_Extensions: _TypeAlias = dict[str, _Mapping[str, _Value]]
_ReadablePath: _TypeAlias = str | bytes | _PathLike[str] | _PathLike[bytes]
_WritablePath: _TypeAlias = str | _PathLike[str]
_ProfileValidators: _TypeAlias = _Mapping[tuple[str, str], _Callable[["Document"], object]]

class _Metadata(_TypedDict):
    """Shape of a structurally valid reserved metadata table; not a runtime export."""
    version: _Literal["0.1"]
    profile: str
    profile_version: str
    requires: _NotRequired[list[str]]

class _DocumentRoot(_TypedDict):
    """Complete typed envelope; application data remains recursively extensible."""
    _ylspec: _Metadata
    data: dict[str, _Value]
    extensions: _NotRequired[_Extensions]

class _SeekableBinaryReader(_Protocol):
    """Minimum synchronous stream interface required by read_at.

    BinaryIO and BytesIO satisfy this protocol. A read must produce bytes, not
    text. The return value of seek is ignored, so custom readers may return None.
    Shared streams require external synchronization during the complete call.
    """

    def read(self, size: int = -1, /) -> bytes: ...
    def seek(self, offset: int, whence: int = 0, /) -> int | None: ...
    def tell(self, /) -> int: ...

class Document:
    """Mutable Python representation of one native-backed YLSpec document.

    The constructor creates the standard envelope. It copies the top-level data
    and extension mappings; nested objects are not deep-copied at construction.
    Edits remain Python values until a native serialization or structural check.
    Serializing revalidates the envelope and detects unsupported values or cycles.

    Parsed documents contain decoded scalar values, lists, dictionaries, and
    exact TemporalValue instances. Constructed documents can additionally contain
    tuples, other string-key mappings, and standard Python date/time objects.
    """

    root: _DocumentRoot
    """Entire mutable envelope; replacing or editing it must preserve the standard shape."""
    limits: Limits
    """Limits applied when dumping, packing, or structurally validating this document."""

    def __init__(
        self,
        data: _Mapping[str, _Value] | None = None,
        *,
        profile: str = "core.data",
        profile_version: str = "0.1",
        extensions: _Mapping[str, _Mapping[str, _Value]] | None = None,
        limits: Limits = ...,
    ) -> None:
        """Create a document using format 0.1 and the supplied profile identity.

        No profile handler, file, or network resource is loaded. Invalid edited
        values are rejected by the native core at serialization/validation time.
        Keys must be strings; None and raw bytes are not valid application values.
        """
        ...

    @property
    def data(self) -> dict[str, _Value]:
        """Return the live application-data dictionary, without copying it.

        Mutations change this document. Use to_dict for a detached copy of the
        entire envelope. Validate the document before relying on profile meaning.
        """
        ...

    @property
    def metadata(self) -> _Metadata:
        """Return the live reserved metadata table, including its profile identity.

        The format version is 0.1. Required capabilities belong in the optional
        requires list. An application's own version belongs under data instead.
        """
        ...

    @property
    def extensions(self) -> _Extensions:
        """Return the live namespaced extension dictionary, creating it if absent.

        Each namespace maps to a table. Optional namespaces survive round trips;
        extensions essential to interpretation should declare required features.
        """
        ...

    def to_dict(self) -> _DocumentRoot:
        """Return a deep copy of the complete root, retaining exact temporal values.

        This is not a JSON conversion: TemporalValue, date/time inputs, tuples,
        NaN, and other supported TOML values are not stringified automatically.
        Mutating the returned tree does not mutate this document.
        """
        ...

    def validate(
        self,
        validators: _ProfileValidators | None = None,
        *,
        features: _Iterable[str] = ...,
    ) -> _Self:
        """Check structure, required capabilities, and the exact selected profile.

        Validators are keyed by (profile_name, profile_version). Each receives
        this document. Returning exactly False rejects it; any other return
        accepts it. Validator exceptions propagate. The core.data/0.1 profile
        needs no registered handler, but required features are still checked.

        Returns self for chaining. Raises UnsupportedError for missing features
        or handlers and ProfileError when a handler returns False. Structural
        errors and serialization limits are checked first through the C core.
        """
        ...

def loads(text: str | bytes, *, limits: Limits = ...) -> Document:
    """Parse a standalone UTF-8 document from text or bytes using the C core.

    Checks TOML 1.1 syntax, source limits, and the reserved envelope. It does not
    validate application-specific profile meaning or authenticate content.
    Unknown profile identities remain readable. The returned document retains
    limits for subsequent serialization and preserves temporal precision.
    """
    ...

def dumps(document: Document) -> str:
    """Serialize a document to UTF-8-compatible TOML text after structural checks.

    Preserves data meaning, not comments, spacing, original table notation, or
    integer radix. The document's limits apply. This is not a cryptographic
    canonicalization format. The operation does not write files or run a profile
    validator. Standard date/time inputs are validated when converted to TOML.
    """
    ...

def load(path: _ReadablePath, *, limits: Limits = ...) -> Document:
    """Read a standalone document from a path in binary mode and parse it.

    Reads at most the configured byte limit plus one byte, allowing oversize
    inputs to fail without loading the rest of the file. Filesystem failures
    propagate as OSError subclasses. The function closes the file it opens.
    For embedded frames or an existing stream, use read_at instead.
    """
    ...

def dump(document: Document, path: _WritablePath) -> None:
    """Serialize and replace a path's contents with UTF-8 document bytes.

    Uses the same checks and serialization policy as dumps. The current adapter
    uses pathlib.Path, so paths are strings or string-valued PathLike objects.
    The write is not an atomic replacement protocol and is not an append operation.
    """
    ...

def pack(document: Document) -> bytes:
    """Return a 32-byte embedding header followed by the serialized document.

    The header records the exact text byte length, frame revision, and encoding.
    It contains no signature, compression, host payload, or locator. The host
    decides where to store the frame and how to record that location. Document
    byte limits exclude the header. Profile approval remains explicit.
    """
    ...

def unpack(buffer: bytes, offset: int = 0, *, limits: Limits = ...) -> Document:
    """Decode one frame at a nonnegative byte offset in an available bytes object.

    Validates the header and declared text length before decoding the document.
    Prefix and trailing host bytes are allowed and are not interpreted. This
    function does not scan for magic or return every frame in a host buffer.
    Use the C API when a consumed-length output is needed.
    """
    ...

def read_at(
    file: _SeekableBinaryReader,
    offset: int = 0,
    *,
    available: int | None = None,
    limits: Limits = ...,
) -> Document:
    """Read a single embedded frame from a synchronous seekable binary stream.

    offset is an absolute byte position. available bounds the enclosing region
    starting there; when omitted, the adapter seeks to EOF to determine it.
    A valid frame causes one 32-byte header read and one exact document read.
    Unrelated host payloads are neither read nor decompressed.

    The original stream position is restored, including on failure. The stream
    remains open. Shared streams require external synchronization. Short reads
    raise OSError; invalid regions, unsupported headers, syntax, and limits use
    the structured document exception hierarchy. Text streams are unsupported.
    """
    ...
