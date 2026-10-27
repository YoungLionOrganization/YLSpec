# YLSpec

[![CI](https://github.com/YoungLionOrganization/YLSpec/actions/workflows/ci.yml/badge.svg)](https://github.com/YoungLionOrganization/YLSpec/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Format: 0.1](https://img.shields.io/badge/format-0.1-orange.svg)](docs/specification.md)
[![Python: 3.11–3.15](https://img.shields.io/badge/Python-3.11%E2%80%933.15-3776AB.svg)](docs/compatibility.md)
[![C: C11](https://img.shields.io/badge/C-C11-555555.svg)](docs/c-api.md)
[![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20macOS%20%7C%20Windows-555555.svg)](docs/compatibility.md)

**Portable metadata documents that work on their own and inside other file formats.**

YLSpec defines a versioned document envelope around TOML 1.1 and an optional,
length-delimited binary frame for embedding that document into another file.
The reference implementation is written in C11. Its Python package uses the same
C core through a native CPython extension.

**Status:** `0.1.0`, experimental. The specification and APIs may change before
1.0. Review the [compatibility policy](docs/compatibility.md) before depending on
an experimental version. A release's support claims are backed by its linked
GitHub Actions run. Private-repository status badges may require GitHub access.

## Why YLSpec?

Applications frequently need the same metadata in several contexts: editable
configuration, a component manifest, or a small record embedded in a larger
binary file. YLSpec gives those contexts a shared document model and an explicit
version boundary.

| Capability | Standalone document | Embedded frame |
|---|---|---|
| Human-editable UTF-8 TOML 1.1 | Yes | The payload is the same text |
| Standard and profile versioning | Yes | Yes |
| Namespaced project extensions | Yes | Yes |
| Exact temporal literals | Yes | Yes |
| Read without touching unrelated host content | Entire document | Header plus declared document bytes |
| Requires an archive or decompressor | No | No |
| Executes embedded code | No | No |

YLSpec does not define plugin execution, package installation, dependency
resolution, signatures, or a host file's layout. Future formats can place YLSpec
frames wherever their own headers or indexes specify.

## Architecture

```mermaid
flowchart LR
    Text["Standalone .ylspec text"] --> Core["C11 document core"]
    Host["Host-supplied offset and region"] --> Frame["32-byte frame decoder"]
    Frame --> Core
    Core --> Values["Typed document values"]
    Values --> Profile["Explicit profile validation"]
    Core --> Python["Native Python API"]
    Core --> CLI["Inspection CLI"]
```

The [embedding guide](docs/embedding.md) explains the byte layout and the host's
responsibilities. The [normative specification](docs/specification.md) defines
document validity independently of the reference implementation.

## Installation

After the first PyPI release, install the native Python package with:

```sh
python -m pip install ylspec
```

Until then, download a wheel from a successful **CI** run's `wheels-*` artifact
and install that wheel with `python -m pip install path/to/the-wheel.whl`.
The release workflow adds published distributions to PyPI; this README does not
display a PyPI version badge before a real project exists.

Native release assets contain both `static/` and `shared/` installations, with
headers, libraries, CLI binaries, CMake package exports, and license notices.
Choose one installation as your CMake prefix:

```cmake
find_package(YLSpec CONFIG REQUIRED)
target_link_libraries(my_application PRIVATE YLSpec::ylspec)
```

See [building](docs/building.md) for source builds and supported toolchains.

## Document example

```toml
[_ylspec]
version = "0.1"
profile = "core.data"
profile_version = "0.1"

[data]
name = "Example component"
enabled = true
platforms = ["linux-x86_64", "windows-x64", "macos-arm64"]

[extensions."xyz.younglion.example"]
channel = "stable"
```

`data` is application-defined. An application's version inside `data` is
independent of the YLSpec format version and the profile version.

## Python quick start

The complete, CI-executed example is [examples/basic.py](examples/basic.py).

```python
import io
import ylspec

document = ylspec.Document({"name": "Example", "enabled": True})
document.validate()

text = ylspec.dumps(document)
restored = ylspec.loads(text)
assert restored.data == document.data

prefix = b"host-defined prefix"
frame = ylspec.pack(document)
host = io.BytesIO(prefix + frame + b"unrelated payload")
metadata = ylspec.read_at(host, offset=len(prefix), available=len(frame))
assert metadata.data["name"] == "Example"
```

`read_at` restores the stream's original position. It reads the 32-byte header
and exactly the document bytes declared in that header. Determining the region
size may seek to the end, but does not read the host payload.

See the [Python API](docs/python-api.md) for types, profile validators, errors,
and exact timestamps. Detailed `__init__.pyi` and `_native.pyi` stubs and a
`py.typed` marker ship with the package for editor completion and static checks;
no separate stub distribution is required.

## C quick start

The complete, CI-executed example is [examples/basic.c](examples/basic.c).

```c
#include <stdio.h>
#include <string.h>
#include <ylspec.h>

int main(void) {
    const char text[] =
        "[_ylspec]\nversion='0.1'\nprofile='core.data'\n"
        "profile_version='0.1'\n[data]\nname='Example'\n";
    yl_document *document = NULL;
    yl_error error = {0};
    if (yl_parse(text, strlen(text), NULL, &document, &error) != YL_OK) {
        fprintf(stderr, "%s\n", error.message);
        return 1;
    }
    yl_document_free(document);
    return 0;
}
```

Lengths are explicit; the input does not need a terminating NUL. The core does
not open files. A host can supply a `yl_read_at_fn` callback to read an embedded
document from a file, mapping, device, or other bounded source.

## Resource limits and trust boundaries

| Property | Default or policy |
|---|---|
| Maximum document text | 16 MiB; configurable |
| Maximum value depth | 64 edges from root; configurable up to 128 |
| Frame header | 32 bytes, little-endian |
| Embedded text | UTF-8 TOML 1.1, uncompressed |
| Integer / float | Signed 64-bit / IEEE-754 binary64 |
| Required feature or profile validation | Explicit; unsupported means failure |
| Integrity and authenticity | Supplied by the host, if needed |

Additional parser limits are listed in [compatibility](docs/compatibility.md).
Parsing does not imply profile approval, cryptographic verification, or
permission to execute host content. See [security](SECURITY.md).

## CLI

```sh
ylspec --version
ylspec validate examples/config.ylspec
ylspec inspect examples/manifest.ylspec
ylspec pack examples/config.ylspec > metadata.bin
ylspec inspect-frame metadata.bin 0
```

See the [CLI reference](docs/cli.md) for commands, output, and exit codes.

## Verification and releases

GitHub Actions builds static/shared C artifacts and Python wheels, runs C and
Python tests, checks TOML 1.1 decoding against `toml-test`, runs sanitizers and
bounded fuzzing, executes documentation examples, and renders Mermaid diagrams.
Benchmark reports record the workload and environment without asserting an
unmeasured speed threshold.

The manually dispatched publish workflow rebuilds and verifies one commit,
creates a draft release, attaches checksummed assets, publishes the same Python
distributions to PyPI using the `PYPI_API_TOKEN` GitHub Actions secret, and then
publishes the GitHub Release.
Read [publishing](docs/publishing.md) before the first release.

## Documentation map

| Guide | Audience |
|---|---|
| [Specification](docs/specification.md) | Independent implementers |
| [Embedding](docs/embedding.md) | Host-format designers |
| [Profiles and extensions](docs/profiles.md) | Application developers |
| [C API and ownership](docs/c-api.md) | C integrators |
| [Python API and types](docs/python-api.md) | Python integrators |
| [CLI](docs/cli.md) | Users inspecting documents |
| [Building](docs/building.md) | Native-library consumers |
| [Compatibility](docs/compatibility.md) | Maintainers and adopters |
| [Publishing](docs/publishing.md) | Release maintainers |

## License and authorship

Copyright 2026 **Cavanşir Qurbanzadə**. Created under **YoungLionOrganization**.
Original project material is licensed under [Apache-2.0](LICENSE).
See [NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md), and
[third-party notices](THIRD_PARTY_NOTICES.md). A document created by a user does
not acquire this project's license merely by using the YLSpec format.
