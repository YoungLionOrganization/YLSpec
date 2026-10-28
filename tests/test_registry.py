# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Registry identity checks protect namespace migrations and OIDC publisher selection."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ylspec_registry", ROOT / "scripts/publish_registry.py")
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)
IDENTITIES = json.loads((ROOT / "release/registries.json").read_text())
VERSION = "0.1.2"


def test_vsix_rejects_previous_publisher_even_with_correct_version(tmp_path):
    path = tmp_path / "extension.vsix"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("extension/package.json", json.dumps({"publisher": "YoungLionOrganization", "name": "ylspec", "version": VERSION}))
    with pytest.raises(ValueError, match="VSIX publisher"):
        registry.validate_asset("vscode", path, VERSION)


def test_vsix_accepts_configured_oidc_publisher(tmp_path):
    path = tmp_path / "extension.vsix"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("extension/package.json", json.dumps({"publisher": IDENTITIES["vscode_publisher"], "name": IDENTITIES["vscode_extension"], "version": VERSION}))
    registry.validate_asset("vscode", path, VERSION)


def maven_bundle(path, group, artifacts):
    with zipfile.ZipFile(path, "w") as archive:
        for artifact in artifacts:
            pom = f'<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion><groupId>{group}</groupId><artifactId>{artifact}</artifactId><version>{VERSION}</version></project>'
            archive.writestr(f"{group.replace('.', '/')}/{artifact}/{VERSION}/{artifact}-{VERSION}.pom", pom)


def test_maven_rejects_previous_group(tmp_path):
    path = tmp_path / "maven.zip"
    maven_bundle(path, "io.github.younglionorganization", IDENTITIES["maven_artifacts"])
    with pytest.raises(ValueError, match="Maven POM coordinates"):
        registry.validate_asset("maven", path, VERSION)


def test_maven_requires_all_publications(tmp_path):
    path = tmp_path / "maven.zip"
    maven_bundle(path, IDENTITIES["maven_group"], IDENTITIES["maven_artifacts"][:-1])
    with pytest.raises(ValueError, match="missing required"):
        registry.validate_asset("maven", path, VERSION)
    maven_bundle(path, IDENTITIES["maven_group"], IDENTITIES["maven_artifacts"])
    registry.validate_asset("maven", path, VERSION)


def test_npm_checks_package_identity_and_version(tmp_path):
    path = tmp_path / "npm.tgz"
    payload = json.dumps({"name": IDENTITIES["npm_package"], "version": VERSION}).encode()
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("package/package.json")
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    registry.validate_asset("npm", path, VERSION)
    with pytest.raises(ValueError, match="npm artifact"):
        registry.validate_asset("npm", path, "0.0.0")
