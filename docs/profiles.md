# Profiles and namespaced extensions

A profile defines what application data means. It does not change TOML syntax,
the document envelope, the frame layout, or core resource limits.

## Choosing a profile

Use `core.data` / `0.1` for unconstrained application data. Configuration and
manifest examples use that profile intentionally: a `version` key under `data`
does not establish package installation or plugin execution behavior.

For stronger constraints, publish a profile specification with:

| Item | Example |
|---|---|
| Identifier | `xyz.example.application` |
| Profile version | `1.0` |
| Required fields | `data.id`, `data.display_name` |
| Field meaning | Stable identifiers versus user-facing labels |
| Extension rules | Which optional values are accepted |
| Validation vectors | Accepted/rejected example documents |
| Compatibility policy | How old readers handle new optional fields |

Identifiers and versions are compared exactly. YLSpec does not fetch schemas
from the network or interpret a version as a URL. Profile documentation and
validation code are maintained by the profile owner.

## Python validator

```python
import ylspec

document = ylspec.Document(
    {"id": "xyz.example.editor", "display_name": "Example Editor"},
    profile="xyz.example.application",
    profile_version="1.0",
)
document.validate({
    ("xyz.example.application", "1.0"):
        lambda doc: bool(doc.data.get("id") and doc.data.get("display_name"))
})
```

An unknown profile remains inspectable through `loads` or `unpack`, but
`validate` raises `UnsupportedError`. This distinction prevents an inert
metadata viewer from needing every application's validation rules.

## C validator

Create a `yl_profile` containing the exact name/version, a callback, and a
caller-owned context. Pass it through a `yl_registry` to `yl_validate`. The
callback returns `YL_OK` or a failure status and fills the supplied error if
needed. There is no process-global profile registration.

## Required features and optional extensions

Put project extensions under `extensions."your.namespace"`. Optional extensions
remain data even when the reader does not understand their meaning. If an
extension is essential, name the required capability in `_ylspec.requires` and
register it in the validation call's supported-feature set.

Supporting a feature is an explicit application claim, not automatic code
loading. A document cannot grant itself capabilities by naming them.
