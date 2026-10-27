# Security

YLSpec reads untrusted metadata. A parsed document is not an authenticated
document, an approved application profile, or authorization to run host content.

Report security issues privately to **cavanshirpro@gmail.com**. Include the
affected version, a minimal input, expected behavior, and the observed failure.
Do not attach secrets or unrelated private payloads. Response timing is best
effort; no fixed service-level guarantee is claimed.

The implementation bounds source size and nesting, validates UTF-8 and frame
lengths, and checks offset arithmetic. Parsing has no network, include, command,
environment-expansion, or plugin-loading behavior. Use host authentication and
explicit profile validation before acting on metadata.

Keep the document/stream stable during a read. Synchronize access to mutable
documents and seekable streams. See the [C ownership guide](docs/c-api.md).
