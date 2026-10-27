# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Static consumer examples, checked against the installed wheel's bundled stubs."""
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Literal, assert_type

import ylspec
from ylspec import _native


def inspect_document(path: Path) -> str:
    document = ylspec.load(path)
    assert_type(document, ylspec.Document)
    assert_type(document.metadata["profile"], str)
    assert_type(document.metadata["version"], Literal["0.1"])
    assert_type(document.validate(), ylspec.Document)
    copied = document.to_dict()
    copied["_ylspec"]["requires"] = ["xyz.example.feature"]
    return ylspec.dumps(document)


document = ylspec.Document(
    {"name": "Example", "enabled": True, "values": [1, 2, 3], "created": date(2026, 10, 27)},
    extensions={"xyz.example": {"channel": "stable"}},
    limits=ylspec.Limits(max_depth=64),
)
document.data["stamp"] = ylspec.TemporalValue("datetime-offset", "2026-10-27T12:34:56.123456789Z")
document.extensions["xyz.other"] = {"enabled": True}
assert_type(ylspec.dumps(document), str)
assert_type(ylspec.pack(document), bytes)
frame = ylspec.pack(document)
assert_type(ylspec.unpack(frame), ylspec.Document)
assert_type(ylspec.read_at(BytesIO(frame), available=len(frame)), ylspec.Document)
assert_type(ylspec.loads(ylspec.dumps(document)), ylspec.Document)


def validate_example(candidate: ylspec.Document) -> bool:
    return isinstance(candidate.data.get("name"), str)


document.validate({("xyz.example", "1.0"): validate_example}, features=["xyz.example.feature"])
native_root = _native.decode(ylspec.dumps(document).encode(), 16_777_216, 64)
assert_type(_native.encode(native_root, 16_777_216, 64, True), bytes)
_, consumed = _native.unpack(frame, 0, 16_777_216, 64)
assert_type(consumed, int)

# Invalid API uses must be rejected; unused-ignore checking detects weakened stubs.
ylspec.dumps({"name": "not a Document"})  # type: ignore[arg-type]
ylspec.loads(123)  # type: ignore[arg-type]
ylspec.read_at("not a binary stream")  # type: ignore[arg-type]
ylspec.TemporalValue("timestamp", "invalid kind")  # type: ignore[arg-type]


class CustomDocument(ylspec.Document):
    pass


assert_type(CustomDocument().validate(), CustomDocument)
