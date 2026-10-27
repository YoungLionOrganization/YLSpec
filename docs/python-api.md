# Python API

The `ylspec` package requires CPython 3.11 or newer and uses its bundled native
extension. Runtime installation has no Python package dependencies. The initial
wheel targets are listed in [compatibility](compatibility.md).

## Documents and values

`Document(data=None, profile="core.data", profile_version="0.1",
extensions=None, limits=Limits())` constructs the standard envelope around a
data mapping. `document.data`, `document.metadata`, and `document.extensions`
are mutable dictionaries. `document.root` contains the complete document.
`document.to_dict()` returns a detached deep copy of that root.

| Python value | TOML meaning |
|---|---|
| `str` | UTF-8 string |
| `bool` | Boolean |
| `int` | Signed 64-bit integer; overflow raises `OverflowError` |
| `float` | Binary64, including infinities and NaN |
| Mapping with string keys | Table |
| `list` or `tuple` | Array |
| `TemporalValue(kind, text)` | Exact validated temporal literal |
| `datetime.date`, `datetime.time`, `datetime.datetime` | Serialized ISO temporal value |
| `None`, bytes as a value, arbitrary objects | Unsupported; raises `TypeError` |

Timezone-aware local `time` is unsupported because TOML has no offset-time type.
Timezone-aware `datetime` becomes an offset datetime. Exact parsed temporal
values remain `TemporalValue`; they do not silently lose precision through a
conversion to Python's microsecond-limited datetime objects.

## Functions

| Function | Result and behavior |
|---|---|
| `loads(text, *, limits=Limits())` | Parse str or bytes into `Document` |
| `dumps(document)` | Revalidate and serialize to str |
| `load(path, *, limits=Limits())` | Read bounded binary text from a path |
| `dump(document, path)` | Write serialized UTF-8 text; replaces that file |
| `pack(document)` | Return a complete frame as bytes |
| `unpack(buffer, offset=0, *, limits=Limits())` | Read one frame from bytes; trailing host bytes are allowed |
| `read_at(file, offset=0, *, available=None, limits=Limits())` | Read one frame from a seekable binary file |

`read_at` uses the C frame decoder through a Python read callback. It restores
the file's original position. If `available` is omitted, it uses the file's
size minus the supplied offset. A truncated underlying read raises `OSError`.
Negative offsets are invalid. Text streams are not supported.

Serialization follows the document's `limits`. Cycles and unsupported values
fail; they are never stringified implicitly. Comments and whitespace are not
retained. See [the executable example](../examples/basic.py).

## Validation and errors

`document.validate(validators=None, *, features=())` first checks structure
through the C core, then checks required capabilities and the selected profile.
Validator keys are `(profile, profile_version)` tuples. A validator receives the
document; returning `False` rejects it, while any other return accepts it. Raised
exceptions propagate. The method returns the document on success.

All structured document errors inherit from `ylspec.Error`, which inherits
`ValueError`. Specialized classes are `ParseError`, `LimitError`, `FrameError`,
`UnsupportedError`, and `ProfileError`. Their attributes are `code`, `offset`,
`line`, and `column`. C allocation failures are reported with code `memory`;
Python-side allocations can raise `MemoryError`. Filesystem errors remain
standard `OSError` subclasses.

Parsing an unknown profile is allowed for inspection; validating it without a
registered handler fails explicitly. See [profiles](profiles.md).
