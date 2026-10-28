# YLSpec for Visual Studio Code

[![Verification](https://github.com/YoungLionOrganization/YLSpec/actions/workflows/ci.yml/badge.svg)](https://github.com/YoungLionOrganization/YLSpec/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/YoungLionOrganization/YLSpec/blob/main/LICENSE)
[![Format](https://img.shields.io/badge/YLSpec-0.1-orange)](https://github.com/YoungLionOrganization/YLSpec/blob/main/docs/specification.md)

Language support for standalone `.ylspec` files. The extension validates documents
with the same C11 reference implementation used by the Python, JavaScript, Java,
and Kotlin libraries, compiled to bundled WebAssembly.

## Features

| Feature | Behavior |
|---|---|
| File association | `.ylspec` opens in the YLSpec language mode |
| Syntax highlighting | Tables, keys, strings, multiline strings, escapes, numbers, temporal literals, booleans, comments |
| Diagnostics | TOML syntax, envelope versions, structure, configured limits, and mandatory features |
| Profile handling | `core.data` is validated; unsupported custom profiles produce a warning and remain editable |
| Metadata completion | Standard keys and their initial values inside `[_ylspec]` |
| Hover documentation | Descriptions of the four standard metadata keys |
| Snippets | `ylspec`, `ylmanifest`, and `ylextension` |
| Commands | **YLSpec: New Document** and **YLSpec: Validate Document** |
| Optional formatter | Canonical semantic serialization through C; removes comments and rewrites whitespace |

Validation runs in a worker thread after a short editing delay. The extension
parses the open document only. It does not execute configuration values, include
files, resolve environment variables, run project tools, or send document content
to a server. No telemetry is collected. WebAssembly and its notices are packaged
inside the VSIX; initialization does not download a parser.

## Install

Download `ylspec-0.1.2.vsix` from a verified
[GitHub Release](https://github.com/YoungLionOrganization/YLSpec/releases).
In VS Code, open **Extensions → … → Install from VSIX…**, then select that file.
Alternatively:

```sh
code --install-extension ylspec-0.1.2.vsix
```

Marketplace availability requires a separately registered publisher and a
successful Marketplace upload. A packaged VSIX is usable without that upload.
The package identifier is `ylvsmp.ylspec`, published by YoungLion (`ylvsmp`).

## Start a document

Run **YLSpec: New Document**, or type `ylspec` in an empty `.ylspec` file and
select the snippet:

```toml
[_ylspec]
version = "0.1"
profile = "core.data"
profile_version = "0.1"

[data]
name = "Example"
enabled = true
```

Application-specific keys belong in `data`. Extra namespaces belong in
`extensions`. The extension does not invent a schema for project data.

## Settings

| Setting | Default | Purpose |
|---|---|---|
| `ylspec.validation.enabled` | `true` | Automatic diagnostics; explicit validation remains available |
| `ylspec.validation.delay` | `350` | Debounce delay in milliseconds; 100–5000 |
| `ylspec.maxDocumentBytes` | `16777216` | UTF-8 source byte limit; configurable up to 64 MiB |
| `ylspec.maxDepth` | `64` | Value depth; maximum 128 |
| `ylspec.format.enabled` | `false` | Enable formatting that discards comments and changes layout |

To opt into semantic formatting and select this formatter:

```json
{
  "ylspec.format.enabled": true,
  "[ylspec]": {
    "editor.defaultFormatter": "ylvsmp.ylspec"
  }
}
```

Formatting preserves values, including exact temporal text and signed 64-bit
integers. Comments, whitespace, literal spelling, and key layout are not retained.
Invalid documents are not reformatted. Automatic format-on-save is not enabled
by the extension.

## Compatibility and scope

VS Code 1.95+ desktop and remote workspace extension hosts are supported. Language
coloring and snippets are declarative; active validation requires a Node-enabled
extension host. Browser-only `vscode.dev` execution is not an advertised target.
Virtual and untrusted workspaces are supported because validation requires no
project execution or arbitrary file access.

Only standalone text documents are edited. Binary `.ylplugin`, `.ylpkg`, frame
discovery, archive editing, custom profile code loading, and embedded payload
modification are outside the extension's scope. Custom profiles need their own
validators in the consuming application; the editor reports their unsupported
validation status as a warning.

## Verification and publishing

The repository workflow tests the real TextMate grammar with Oniguruma, tests
Unicode diagnostic positions, launches a VS Code Extension Host under a virtual
display, and verifies diagnostics, completions, formatting, and the bundled C
engine. It then packages the universal VSIX as a required release asset.

See the repository's
[editor guide](https://github.com/YoungLionOrganization/YLSpec/blob/main/docs/vscode.md)
and [registry publishing guide](https://github.com/YoungLionOrganization/YLSpec/blob/main/docs/registries.md)
for reproducible packaging and account setup.

## License

Copyright 2026 Cavanşir Qurbanzadə. Original code and documentation are licensed
under Apache-2.0. The bundled tomlc17 parser retains its MIT license and original
notice in `engine/licenses/tomlc17/LICENSE`. See the distributed `NOTICE` and
`THIRD_PARTY_NOTICES.md` files.
