# Building and consuming YLSpec

## Requirements

| Component | Requirement |
|---|---|
| C compiler | C11; GCC, Clang, or MSVC |
| CMake | 3.26 or newer |
| Python package build | CPython 3.11+, pip with PEP 517 support |
| Python backend | scikit-build-core 0.11.x |
| Runtime Python dependencies | None |

The TOML parser is vendored at a recorded commit. Consumer builds do not fetch
source code from upstream. GitHub Actions performs project verification and
produces distributable artifacts; contributors need not run resource-intensive
verification on their personal machine.

## Native builds

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
cmake --build build --config Release
cmake --install build --config Release --prefix /your/install/prefix
```

Select `BUILD_SHARED_LIBS=ON` for a shared library. On Windows this produces a DLL
and import library. `YLSPEC_BUILD_CLI=OFF` disables the filesystem adapter and
CLI. `BUILD_TESTING=OFF` disables test and conformance executables.

Applications consume the installed export using `find_package(YLSpec CONFIG
REQUIRED)` and `YLSpec::ylspec`. Use the selected installation's prefix as
`CMAKE_PREFIX_PATH`. The target supplies the required include path and shared
library import definitions. The C ABI is experimental during 0.x.

Native release archives separate `static/` and `shared/` installations, each
with an independent CMake package. On Windows, ensure a shared installation's
`bin` directory is discoverable when running its CLI or your application.

## Python builds

```sh
python -m pip install .
```

The backend builds the native extension and links the core statically into the
wheel. Wheels do not include the CLI or require a separately installed
`libylspec`. The source distribution includes the C core, public header,
vendored parser, build files, and license notices.

## GitHub verification controls

| CMake option | Purpose |
|---|---|
| `YLSPEC_SANITIZE=ON` | ASan/UBSan checks with a supported compiler |
| `YLSPEC_FUZZ=ON` | Clang/libFuzzer text and frame entry point |
| `YLSPEC_BUILD_PYTHON=ON` | Limited-API CPython extension |

The reusable verification workflow builds and tests each native target, tests
minimum-ABI wheels across supported CPython versions, checks decoding through
`toml-test` v2.2.0, renders documentation diagrams, checks source notices, and
uploads benchmark information. Release publishing calls the same workflow so
it cannot bypass these gates.
