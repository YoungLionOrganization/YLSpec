# Third-party notices

Original YLSpec material: Copyright 2026 Cavanşir Qurbanzadə, Apache-2.0.

## tomlc17

| Property | Value |
|---|---|
| Author | CK Tan |
| Copyright | Copyright (c) 2024-2026, CK Tan |
| License | MIT |
| Upstream | https://github.com/cktan/tomlc17 |
| Pinned commit | `4987cf895df61f702d19e3481f34b032ab29ed3a` |
| Files | `vendor/tomlc17/tomlc17.c`, `tomlc17.h`, `conformance.c`, `LICENSE` |

The complete upstream license is in [vendor/tomlc17/LICENSE](vendor/tomlc17/LICENSE).
The conformance driver originates from upstream `test/stdtest/parser.c`.

Local modifications: raise the dotted-key component limit to 129 and the parser's
bracket/brace ceilings to 128, enabling YLSpec's documented configurable depth;
adjust the conformance driver's include path and cast `isprint` arguments to
`unsigned char`. The YLSpec document depth limit is enforced separately.

YLSpec validates UTF-8 before parsing and retains temporal source literals rather
than relying on the parser's microsecond-resolution timestamp representation.
The upstream parser also has implementation limits: 16,384 entries per table or
array and bounded numeric/temporal literal buffers. These are documented in the
[compatibility guide](docs/compatibility.md).

## Verification tooling

GitHub Actions installs the separately licensed `toml-test` v2.2.0 test harness,
Python packaging tools, and Mermaid CLI. They are build/test tools, not runtime
dependencies bundled in YLSpec. Vendored dependency notices are included in native
packages, source distributions, and wheels.
