# Changelog

## 0.1.2

Align Maven publications with `xyz.younglion` and the VS Code extension with
`ylvsmp.ylspec`. Enable Marketplace OIDC Trusted Publishing, centralize registry
identities, and reject mismatched publisher/group/version metadata before upload.
Preserve Java package names, native entry points, and document/frame format 0.1.

See the [distribution migration notes](release/notes/v0.1.2.md).

## 0.1.1

Native Node-API and browser WebAssembly clients with TypeScript contracts;
JNI-backed Java and Kotlin APIs; Android API 26+ native AAR; shared typed binding
transport; corrected validation after mutation; and npm/Maven publication
workflows. Document format 0.1 and the existing frame layout are unchanged.

VS Code language tools add syntax coloring, snippets, metadata completion,
hover documentation, worker-based C validation, and opt-in semantic formatting.
The universal VSIX and its Marketplace upload workflow join the release assets.
Callback readers reject invalid lengths before requesting document payloads;
adapter tests cover multiple unaligned frames and header-only rejection.

See the [patch release notes](release/notes/v0.1.1.md).

## 0.1.0

Initial experimental implementation of the YLSpec document envelope and 32-byte
embedding frame, with a portable C11 library, native Python package, CLI,
profile callbacks, and GitHub-hosted verification and publishing workflows.

See the [detailed release notes](release/notes/v0.1.0.md) for compatibility,
artifacts, installation, and limitations. Version entries describe source
changes; a published GitHub Release and PyPI files determine publication status.
