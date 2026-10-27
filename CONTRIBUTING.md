# Contributing

Discuss behavior or format changes in an issue before proposing a large change.
Keep all repository content in English, with original spelling for proper names.

## Specification changes

Describe the problem, affected document/frame/profile version, before/after
examples, compatibility impact, and accepted/rejected test vectors. Distinguish
normative requirements from informative examples. A reference-code behavior
change alone does not silently amend the standard.

The primary maintainer reviews proposals. Decisions and rationale belong in the
issue or pull request. Before 1.0, accepted breaking changes require release
notes and migration guidance. See [compatibility](docs/compatibility.md).

## Implementation changes

Use portable C11 and the existing C API ownership model. Avoid implicit I/O,
global registries, or platform code in the core. Add focused tests for changed
behavior, update public examples and documentation, and let GitHub Actions run
builds and verification. External actions and vendored dependencies must be
pinned with provenance and original notices.

Submit contributions under Apache-2.0. By submitting original work for inclusion,
you license that contribution under the project's license, including its
applicable patent terms. Do not submit work you are not authorized to license.
This policy does not claim that third-party patents cannot exist or that
Apache's contribution-specific grant is an unlimited standards patent promise.

## Release changes

Update `release/release.json` and its detailed notes together. Keep the release
version authoritative and avoid committing compiled assets. Publication follows
the explicit [publishing workflow](docs/publishing.md).
