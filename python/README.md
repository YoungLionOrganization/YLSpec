# YLSpec for Python

[![PyPI](https://img.shields.io/pypi/v/ylspec)](https://pypi.org/project/ylspec/)
[![Python](https://img.shields.io/pypi/pyversions/ylspec)](https://pypi.org/project/ylspec/)
[![Distributions](https://img.shields.io/pypi/format/ylspec)](https://pypi.org/project/ylspec/#files)
[![CI](https://github.com/YoungLionOrganization/YLSpec/actions/workflows/ci.yml/badge.svg)](https://github.com/YoungLionOrganization/YLSpec/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/YoungLionOrganization/YLSpec/blob/main/LICENSE)

**One document model for configuration, manifests, and embedded metadata.**
YLSpec is a typed Python interface to the portable C11 reference implementation.
Standalone `.ylspec` files use UTF-8 TOML 1.1. A small binary frame embeds the same
document at a host-supplied offset, without reading or decompressing host payloads.

Created by **Cavanşir Qurbanzadə**, maintained under
[YoungLionOrganization](https://github.com/YoungLionOrganization).
Contact: [cavanshirpro@gmail.com](mailto:cavanshirpro@gmail.com).
This is an experimental 0.1 series implementation; document and frame formats
remain at 0.1 independently of the package version.

## Install

```sh
python -m pip install ylspec
```

CPython 3.11–3.15 is supported through the CPython 3.11 stable ABI. Published wheels
cover Windows x64, Linux x86_64/ARM64 (manylinux and musllinux), and macOS Intel and
Apple Silicon. A source installation requires a C11 compiler and CMake. Runtime
Python dependencies are not required. Complete `.pyi` stubs and `py.typed` ship
inside the package.

## Standalone documents

```python
import ylspec

document = ylspec.Document({"name": "Example", "enabled": True, "count": 42})
document.validate()
text = ylspec.dumps(document)
restored = ylspec.loads(text)
assert restored.data == document.data
assert restored.metadata["profile"] == "core.data"
```

`load(path)` and `dump(document, path)` provide filesystem adapters. The document
contains `_ylspec`, `data`, and optional namespaced `extensions`. Application
values belong in `data`; applications can register profile validators explicitly.
Unknown profiles remain readable without importing application code.

## Embedded metadata

```python
import io
import ylspec

document = ylspec.Document({"name": "Plugin metadata", "enabled": True})
frame = ylspec.pack(document)
prefix = b"host-prefix"
stream = io.BytesIO(prefix + frame + b"unrelated host payload")
stream.seek(3)
embedded = ylspec.read_at(stream, offset=len(prefix), available=len(frame))
assert embedded.data == document.data
assert stream.tell() == 3
assert ylspec.unpack(prefix + frame, offset=len(prefix)).data == document.data
```

The host records the offset and enclosing region. A successful read requests
only the 32-byte header and declared document bytes. Frames do not authenticate
content and do not define a plugin/package container or execution model.

## Types, errors, and limits

| TOML value | Python representation |
|---|---|
| String / boolean | `str` / `bool` |
| Integer / float | Signed 64-bit `int` / binary64 `float` |
| Array / table | `list` / `dict[str, value]` |
| Date / time / timestamp | `TemporalValue(kind, text)` with exact fractional precision |

Standard `datetime.date`, `datetime.time`, and `datetime.datetime` objects are
accepted when writing. TOML has no null value. Serialization preserves value
meaning; comments, whitespace, and original literal spelling are not retained.

`Limits()` defaults to 16 MiB of document text and 64 nesting edges. Structured
exceptions include `ParseError`, `FrameError`, `LimitError`, `UnsupportedError`,
and `ProfileError`, with codes, byte offsets, and source positions when available.
Ordinary argument and filesystem failures use standard Python exceptions.
Reading never executes commands, expands environment variables, includes files,
or accesses the network.

## Documentation and ownership

- [Python API, ownership, and complete type contracts](https://github.com/YoungLionOrganization/YLSpec/blob/main/docs/python-api.md)
- [Normative document specification](https://github.com/YoungLionOrganization/YLSpec/blob/main/docs/specification.md)
- [Embedding integration and frame byte layout](https://github.com/YoungLionOrganization/YLSpec/blob/main/docs/embedding.md)
- [Compatibility and migration policy](https://github.com/YoungLionOrganization/YLSpec/blob/main/docs/compatibility.md)
- [Release history and checksummed assets](https://github.com/YoungLionOrganization/YLSpec/releases)
- [Report an issue](https://github.com/YoungLionOrganization/YLSpec/issues)

Package identity is available through `ylspec.__author__`, `__maintainer__`,
`__email__`, `__license__`, `__copyright__`, `__url__`, and `__version__`.
For installed distribution metadata, use `importlib.metadata.metadata("ylspec")`.

Copyright 2026 **Cavanşir Qurbanzadə**. Original code, tests, and documentation
are licensed under [Apache-2.0](https://github.com/YoungLionOrganization/YLSpec/blob/main/LICENSE).
The vendored tomlc17 parser retains its MIT license. Distribution files include
the original notices; see [third-party attribution](https://github.com/YoungLionOrganization/YLSpec/blob/main/THIRD_PARTY_NOTICES.md).
