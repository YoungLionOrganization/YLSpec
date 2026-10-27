# CLI reference

The native CLI is named `ylspec` (`ylspec.exe` on Windows). It uses the same core
as the C library and Python extension. All messages are English.

| Command | Output |
|---|---|
| `ylspec --version` | Library release version |
| `ylspec validate DOCUMENT` | Success message after core profile validation |
| `ylspec inspect DOCUMENT` | Reserialized, structurally valid TOML |
| `ylspec pack DOCUMENT` | Binary frame on stdout |
| `ylspec inspect-frame FILE OFFSET` | Reserialized document from the given decimal offset |

Inspection parses the envelope but does not approve an unknown application
profile. `validate` has no plugin-loading or external-validator option in 0.1;
it supports the built-in `core.data` / `0.1` profile without extra required
features. Use the C/Python APIs to register application validators.

## Examples

```sh
ylspec validate examples/config.ylspec
ylspec inspect examples/manifest.ylspec
ylspec pack examples/config.ylspec > metadata.bin
ylspec inspect-frame metadata.bin 0
```

`pack` writes binary bytes, so redirect to a binary-safe file destination. On
Windows the CLI explicitly sets stdout to binary mode for this command. Older
shells may transform native-program redirection; Python's `pack` and a binary
file write avoid shell-dependent behavior.

## Errors

| Exit code | Meaning |
|---:|---|
| 0 | Success |
| 1 | Invalid document, frame, unsupported profile, I/O, allocation, or limit error |
| 2 | Usage error or invalid command/offset argument |

Core errors are printed to stderr with their status name and available source
position. No command modifies its input file. Default core limits apply.
