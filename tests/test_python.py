# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import io
import math
import struct
from importlib.resources import files
from importlib.metadata import metadata
from email.utils import getaddresses
from datetime import date, datetime, time, timezone
import pytest
import ylspec

PREFIX = "[_ylspec]\nversion='0.1'\nprofile='core.data'\nprofile_version='0.1'\n[data]\n"


def test_installed_package_identity_and_distribution_metadata():
    info = metadata("ylspec")
    assert info["Version"] == ylspec.__version__
    assert info["License-Expression"] == ylspec.__license__ == "Apache-2.0"
    assert info["Author"] == ylspec.__author__
    assert ("Cavanshirpro", ylspec.__email__) in getaddresses(info.get_all("Author-email"))
    assert ylspec.__author__ in info["Maintainer"]
    assert not any("=?" in str(info[field]) for field in ("Author", "Author-email", "Maintainer", "Maintainer-email"))
    assert ylspec.__copyright__ == "Copyright 2026 Cavanşir Qurbanzadə"
    assert "YoungLionOrganization" in ylspec.__maintainer__
    assert "Repository, " + ylspec.__url__ in info.get_all("Project-URL")
    assert "# YLSpec for Python" in (info.get("Description") or info.get_payload())


@pytest.mark.parametrize("field", ["max_document_bytes", "max_depth"])
@pytest.mark.parametrize("value", [True, False, 1.5, "64"])
def test_limits_reject_noninteger_configuration(field, value):
    with pytest.raises(TypeError):
        ylspec.Limits(**{field: value})


@pytest.mark.parametrize("value,error", [(True, TypeError), (1.5, TypeError), ("0", TypeError),
                                        (-1, ValueError), (1 << 64, OverflowError), ((1 << 64) + 7, OverflowError)])
def test_offsets_cannot_wrap_into_valid_frames(value, error):
    frame = ylspec.pack(ylspec.Document({"x": 1}))
    with pytest.raises(error):
        ylspec.unpack(frame, value)
    stream = Tracked(frame)
    stream.seek(3)
    with pytest.raises(error):
        ylspec.read_at(stream, value, available=len(frame))
    assert stream.tell() == 3
    assert stream.reads == []


@pytest.mark.parametrize("value,error", [(True, TypeError), (1.5, TypeError), (-1, ylspec.FrameError),
                                        (1 << 64, OverflowError)])
def test_region_sizes_are_validated_before_stream_reads(value, error):
    stream = Tracked(ylspec.pack(ylspec.Document()))
    stream.seek(3)
    with pytest.raises(error):
        ylspec.read_at(stream, available=value)
    assert stream.tell() == 3
    assert stream.reads == []


def test_inferred_stream_region_cannot_wrap_and_restores_position():
    class OversizedStream(Tracked):
        def tell(self):
            return (1 << 64) if super().tell() == len(self.getvalue()) else super().tell()
    stream = OversizedStream(ylspec.pack(ylspec.Document()))
    stream.seek(3)
    with pytest.raises(OverflowError):
        ylspec.read_at(stream)
    assert stream.tell() == 3
    assert stream.reads == []


@pytest.mark.parametrize("writer", [ylspec.dumps, ylspec.pack])
def test_serializers_reject_non_documents_consistently(writer):
    with pytest.raises(TypeError, match="Expected Document"):
        writer({"name": "example"})


def test_installed_package_includes_documented_type_stubs():
    package = files("ylspec")
    for name in ("__init__.pyi", "_native.pyi", "py.typed"):
        assert package.joinpath(name).is_file(), f"Missing installed typing resource: {name}"


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
