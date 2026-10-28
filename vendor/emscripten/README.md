# WebAssembly runtime notices

These unmodified notice files accompany the runtime portions linked into or
emitted alongside YLSpec's WebAssembly build. The full Emscripten SDK is not
vendored here.

| Property | Value |
|---|---|
| Emscripten release | `6.0.13` |
| Emscripten immutable commit | `e13ee988ce3d87a738dd8f3661d02223308c412a` |
| SDK repository commit used by CI | `35659964bc2762fffec0d257997fb61475f765b7` |
| Upstream | https://github.com/emscripten-core/emscripten |
| Files | `LICENSE`, `AUTHORS`, `system/lib/libc/musl/COPYRIGHT`, `system/lib/compiler-rt/LICENSE.TXT` |

`musl-COPYRIGHT` and `compiler-rt-LICENSE.TXT` retain their complete upstream
contents under distinct local filenames. Original dependency copyright dates
and license terms are preserved. The packaging scripts copy these files into
the npm package's `licenses/emscripten/` and the VSIX's
`engine/licenses/emscripten/` directories.

This provenance note is Copyright 2026 Cavanşir Qurbanzadə,
SPDX-License-Identifier: Apache-2.0. It does not replace or relicense the original
notice files.
