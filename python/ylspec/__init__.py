# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Standalone and embeddable YLSpec documents, backed by the C reference library."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable, Mapping
from . import _native

__version__ = _native.__version__
__all__ = ["Document", "TemporalValue", "Limits", "Error", "ParseError", "LimitError",
           "FrameError", "UnsupportedError", "ProfileError", "loads", "dumps", "load",
           "dump", "pack", "unpack", "read_at", "__version__"]


class Error(ValueError):
    """Structured C-core error; offsets are relative to the document payload."""
    def __init__(self, message: str, *, code: str = "invalid", offset: int = 0,
                 line: int = 0, column: int = 0):
        super().__init__(message)
        self.code, self.offset, self.line, self.column = code, offset, line, column


class ParseError(Error):
    """Invalid text syntax or encoding."""


class LimitError(Error):
    """Configured resource limit exceeded."""


class FrameError(Error):
    """Malformed or truncated embedding frame."""


class UnsupportedError(Error):
    """Unsupported format, encoding, required feature, or profile."""


class ProfileError(Error):
    """Profile validation failed."""


@dataclass(frozen=True)
class Limits:
    max_document_bytes: int = 16 * 1024 * 1024
    max_depth: int = 64

    def __post_init__(self):
        if not 0 < self.max_document_bytes <= (1 << 63) - 1 or not 0 < self.max_depth <= 128:
            raise ValueError("Limits must be positive; maximum supported depth is 128")


@dataclass(frozen=True)
class TemporalValue:
    """Exact TOML temporal literal, including all fractional-second digits."""
    kind: str
    text: str


def _call(function, *args):
    try:
        return function(*args)
    except ValueError as exc:
        if len(exc.args) == 6 and isinstance(exc.args[0], int):
            _, code, offset, line, column, message = exc.args
            error_type = {"syntax": ParseError, "limit": LimitError, "frame": FrameError,
                          "unsupported": UnsupportedError, "profile": ProfileError}.get(code, Error)
            raise error_type(message, code=code, offset=offset, line=line, column=column) from None
        raise


def _decode(value):
    if isinstance(value, tuple):
        return TemporalValue(value[0], value[1].decode("utf-8"))
    if isinstance(value, dict):
        return {key: _decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode(item) for item in value]
    return value


def _encode(value, depth=0):
    if depth > 128:
        raise LimitError("Maximum construction depth exceeded", code="limit")
    if isinstance(value, TemporalValue):
        return value.kind, value.text.encode("utf-8")
    if isinstance(value, datetime):
        return ("datetime-offset" if value.utcoffset() is not None else "datetime", value.isoformat().encode("ascii"))
    if isinstance(value, time):
        if value.utcoffset() is not None:
            raise ValueError("TOML local time cannot have a timezone offset")
        return "time", value.isoformat().encode("ascii")
    if isinstance(value, date):
        return "date", value.isoformat().encode("ascii")
    if isinstance(value, Mapping):
        return {key: _encode(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(item, depth + 1) for item in value]
    return value


class Document:
    """Mutable owned Python representation; serialization revalidates its structure."""
    def __init__(self, data: Mapping[str, Any] | None = None, *, profile="core.data",
                 profile_version="0.1", extensions=None, limits: Limits = Limits()):
        self.root = {"_ylspec": {"version": "0.1", "profile": profile, "profile_version": profile_version},
                     "data": dict(data or {})}
        if extensions is not None:
            self.root["extensions"] = dict(extensions)
        self.limits = limits

    @classmethod
    def _from_root(cls, root, limits):
        document = cls(limits=limits)
        document.root = _decode(root)
        return document

    @property
    def data(self):
        return self.root["data"]

    @property
    def metadata(self):
        return self.root["_ylspec"]

    @property
    def extensions(self):
        return self.root.setdefault("extensions", {})

    def to_dict(self):
        """Return a detached copy of the entire document, preserving TemporalValue."""
        from copy import deepcopy
        return deepcopy(self.root)

    def validate(self, validators: Mapping[tuple[str, str], Callable] | None = None, *, features=()):
        # Revalidate structural edits in the C core before profile-specific validation.
        dumps(self)
        required = self.metadata.get("requires", [])
        missing = set(required) - set(features)
        if missing:
            raise UnsupportedError("Unsupported required features: " + ", ".join(sorted(missing)), code="unsupported")
        key = self.metadata["profile"], self.metadata["profile_version"]
        if key == ("core.data", "0.1"):
            return self
        validator = (validators or {}).get(key)
        if validator is None:
            raise UnsupportedError("Unsupported profile: " + "/".join(key), code="unsupported")
        if validator(self) is False:
            raise ProfileError("Profile validator rejected document", code="profile")
        return self


def loads(text: str | bytes, *, limits: Limits = Limits()) -> Document:
    if isinstance(text, str):
        text = text.encode("utf-8")
    return Document._from_root(_call(_native.decode, text, limits.max_document_bytes, limits.max_depth), limits)


def dumps(document: Document) -> str:
    if not isinstance(document, Document):
        raise TypeError("Expected Document; use Document(data) to construct one")
    return _call(_native.encode, _encode(document.root), document.limits.max_document_bytes,
                 document.limits.max_depth, False).decode("utf-8")


def load(path, *, limits: Limits = Limits()) -> Document:
    with open(path, "rb") as stream:
        text = stream.read(limits.max_document_bytes + 1)
    return loads(text, limits=limits)


def dump(document: Document, path) -> None:
    Path(path).write_bytes(dumps(document).encode("utf-8"))


def pack(document: Document) -> bytes:
    return _call(_native.encode, _encode(document.root), document.limits.max_document_bytes,
                 document.limits.max_depth, True)


def unpack(buffer: bytes, offset: int = 0, *, limits: Limits = Limits()) -> Document:
    if offset < 0:
        raise ValueError("Offset must be nonnegative")
    root, _ = _call(_native.unpack, buffer, offset, limits.max_document_bytes, limits.max_depth)
    return Document._from_root(root, limits)


def read_at(file, offset: int = 0, *, available: int | None = None, limits: Limits = Limits()) -> Document:
    """Read a frame from a seekable binary file; restore the original position."""
    if offset < 0:
        raise ValueError("Offset must be nonnegative")
    original = file.tell()
    try:
        if available is None:
            file.seek(0, 2)
            available = file.tell() - offset
        if available < 0:
            raise FrameError("Invalid frame region", code="frame")
        def reader(position, size):
            file.seek(position)
            return file.read(size)
        root = _call(_native.read_at, reader, offset, available, limits.max_document_bytes, limits.max_depth)
        return Document._from_root(root, limits)
    finally:
        file.seek(original)
