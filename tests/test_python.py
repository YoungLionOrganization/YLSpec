# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import io
import math
import struct
from datetime import date, datetime, time, timezone
import pytest
import ylspec

PREFIX = "[_ylspec]\nversion='0.1'\nprofile='core.data'\nprofile_version='0.1'\n[data]\n"


def test_roundtrip_and_exact_temporal():
    text = PREFIX + 'stamp=2026-10-27T12:34:56.123456789123Z\n"nul\\u0000key"="a\\u0000b"\nvalues=[1,true,2.5]\n'
    doc = ylspec.loads(text).validate()
    assert doc.data["stamp"] == ylspec.TemporalValue("datetime-offset", "2026-10-27T12:34:56.123456789123Z")
    assert doc.data["nul\0key"] == "a\0b"
    assert ylspec.loads(ylspec.dumps(doc)).to_dict() == doc.to_dict()
    assert ylspec.unpack(ylspec.pack(doc)).to_dict() == doc.to_dict()


def test_construction_and_mutation(tmp_path):
    doc = ylspec.Document({"message": "Hello 🌍", "date": date(2026, 10, 27),
                           "time": time(12, 34, 56), "stamp": datetime(2026, 10, 27, tzinfo=timezone.utc)})
    doc.data["number"] = -(1 << 63)
    doc.extensions["xyz.example"] = {"enabled": True}
    path = tmp_path / "config.ylspec"
    ylspec.dump(doc, path)
    restored = ylspec.load(path)
    assert restored.data["number"] == -(1 << 63)
    assert restored.data["date"].text == "2026-10-27"
    assert restored.data["message"] == "Hello 🌍"
    assert restored.extensions["xyz.example"]["enabled"]


class Tracked(io.BytesIO):
    def __init__(self, buffer):
        super().__init__(buffer)
        self.reads = []

    def read(self, size=-1):
        self.reads.append((self.tell(), size))
        return super().read(size)


def test_bounded_reads_and_multiple_frames():
    one, two = ylspec.pack(ylspec.Document({"name": "one"})), ylspec.pack(ylspec.Document({"name": "two"}))
    start = 7
    file = Tracked(b"prefix!" + one + two + b"X" * 100000)
    file.seek(3)
    assert ylspec.read_at(file, start, available=len(one)).data["name"] == "one"
    assert file.reads == [(start, 32), (start + 32, len(one) - 32)]
    assert file.tell() == 3
    assert ylspec.read_at(file, start + len(one)).data["name"] == "two"
    assert ylspec.unpack(file.getvalue(), start + len(one)).data["name"] == "two"


def test_all_truncated_frames_and_bad_headers():
    frame = ylspec.pack(ylspec.Document({"x": 1}))
    for end in range(len(frame)):
        with pytest.raises(ylspec.Error):
            ylspec.unpack(frame[:end])
    for offset, value in [(0, 0), (8, 1), (10, 2), (12, 33), (24, 2), (28, 1)]:
        altered = bytearray(frame)
        altered[offset] = value
        with pytest.raises(ylspec.Error):
            ylspec.unpack(bytes(altered))
    altered = bytearray(frame)
    struct.pack_into("<Q", altered, 16, (1 << 64) - 1)
    with pytest.raises(ylspec.LimitError):
        ylspec.unpack(bytes(altered))


def test_limits_profiles_and_required_features():
    with pytest.raises(ylspec.LimitError):
        ylspec.loads(PREFIX + "x=1", limits=ylspec.Limits(max_document_bytes=10))
    with pytest.raises(ylspec.LimitError):
        ylspec.loads(PREFIX + "x=[[[1]]]", limits=ylspec.Limits(max_depth=2))
    doc = ylspec.Document({"x": 1}, profile="xyz.example", profile_version="1")
    with pytest.raises(ylspec.UnsupportedError):
        doc.validate()
    doc.validate({("xyz.example", "1"): lambda document: document.data["x"] == 1})
    doc.metadata["requires"] = ["xyz.example.feature"]
    with pytest.raises(ylspec.UnsupportedError):
        doc.validate({("xyz.example", "1"): lambda d: True})
    doc.validate({("xyz.example", "1"): lambda d: True}, features=["xyz.example.feature"])


@pytest.mark.parametrize("text", [PREFIX + "x=1\nx=2", PREFIX + "x='unterminated", PREFIX.encode() + b"x='\xff'", "", PREFIX + "x=01"])
def test_invalid_documents(text):
    with pytest.raises(ylspec.Error):
        ylspec.loads(text)


def test_unsupported_types_cycles_and_temporal_injection():
    with pytest.raises(TypeError):
        ylspec.dumps(ylspec.Document({"x": None}))
    with pytest.raises(OverflowError):
        ylspec.dumps(ylspec.Document({"x": 1 << 63}))
    doc = ylspec.Document()
    doc.data["cycle"] = doc.data
    with pytest.raises(ylspec.LimitError):
        ylspec.dumps(doc)
    with pytest.raises(ValueError):
        ylspec.dumps(ylspec.Document({"x": ylspec.TemporalValue("date", "2026-10-27 # comment")}))


def test_toml_11_and_special_values():
    doc = ylspec.loads(PREFIX + 'x={\n a="\\e\\x41",\n}\ny=nan\nz=-inf\nt=12:34\n')
    assert doc.data["x"]["a"] == "\x1bA"
    assert math.isnan(doc.data["y"]) and doc.data["z"] == -math.inf
    assert ylspec.loads(ylspec.dumps(doc)).data["t"].text == "12:34"
    with pytest.raises(ylspec.ParseError):
        ylspec.loads(PREFIX + 'μ="requires quotes"')
    assert ylspec.loads(PREFIX + '"μ"="quoted Unicode key"').data["μ"] == "quoted Unicode key"


def test_error_positions_and_stream_failure():
    with pytest.raises(ylspec.ParseError) as caught:
        ylspec.loads(PREFIX + "x=bad")
    assert caught.value.line == 6 and caught.value.column == 1
    assert caught.value.offset == len(PREFIX)
    file = io.BytesIO(b"bad")
    file.seek(1)
    with pytest.raises(ylspec.FrameError):
        ylspec.read_at(file)
    assert file.tell() == 1
