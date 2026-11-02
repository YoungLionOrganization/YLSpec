# Organization publishing secrets

YLSpec's manual publishing workflows use the same GitHub expression for inherited
organization secrets: `secrets.NAME`. There is no special `organization.secrets`
syntax and no credential is copied into source or workflow outputs.

Grant `YoungLionOrganization/YLSpec` access to these organization Actions secrets:

| Secret | Workflow / purpose |
|---|---|
| `PYPI_API_TOKEN` | Publish release / PyPI package upload |
| `NPM_TOKEN` | Publish npm package / scoped npm publishing permission |
| `MAVEN_CENTRAL_USERNAME`, `MAVEN_CENTRAL_PASSWORD` | Central Portal generated user-token pair |
| `MAVEN_GPG_PRIVATE_KEY`, `MAVEN_GPG_PASSPHRASE` | OpenPGP signing, separate from registry authentication |

Remove obsolete repository secrets with these names: repository values override
organization values. Environment secrets take precedence too; check the `pypi`
environment if its configuration contains an old override. Registry permissions
still apply: a project-scoped PyPI token cannot publish another project, and npm
tokens must allow the configured scope/package. Sharing storage does not extend
a registry credential's permissions.

Run **Check inherited publishing secrets** from Actions after changing access.
It reports names and availability only; it neither validates credentials against
registries nor publishes packages. The workflow cannot identify the storage
level of an overridden value, so remove overrides through GitHub settings first.
Never log, export through Actions outputs, or paste secret values into an issue.

Publication remains an explicit manual action using the existing verification,
release and immutable-artifact gates. Moving secrets does not change versions,
package names, signing identities or the published package bytes.
