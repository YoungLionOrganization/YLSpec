# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Publish already verified release assets without rebuilding their binary payloads."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(kind):
    version = os.environ.get("INPUT_VERSION") or json.loads((ROOT / "release/release.json").read_text())["version"]
    if not re.fullmatch(r"0\.[0-9]+\.[0-9]+", version):
        raise ValueError("Expected an explicit 0.MINOR.PATCH version")
    repo = os.environ["GITHUB_REPOSITORY"]
    release = json.loads(subprocess.check_output(["gh", "release", "view", "v" + version, "--repo", repo, "--json", "isDraft"]))
    if release["isDraft"]:
        raise ValueError("Registry publication requires a published GitHub Release")
    filename = f"younglionorganization-ylspec-{version}.tgz" if kind == "npm" else f"ylspec-jvm-{version}.zip"
    destination = ROOT / "dist/registry"
    destination.mkdir(parents=True, exist_ok=True)
    for pattern in (filename, "SHA256SUMS"):
        subprocess.run(["gh", "release", "download", "v" + version, "--repo", repo, "--pattern", pattern, "--dir", str(destination)], check=True)
    checksums = dict((line.split("  ", 1)[1], line.split("  ", 1)[0]) for line in (destination / "SHA256SUMS").read_text().splitlines())
    with (destination / filename).open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if checksums.get(filename) != actual:
        raise ValueError("Release asset SHA-256 mismatch")
    with open(os.environ["GITHUB_ENV"], "a") as environment:
        environment.write(f"REGISTRY_VERSION={version}\nREGISTRY_ASSET={destination / filename}\n")


def central():
    username, password = os.environ["MAVEN_CENTRAL_USERNAME"], os.environ["MAVEN_CENTRAL_PASSWORD"]
    private_key = os.environ["MAVEN_GPG_PRIVATE_KEY"]
    passphrase = os.environ.get("MAVEN_GPG_PASSPHRASE", "")
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    version = os.environ["REGISTRY_VERSION"]
    with tempfile.TemporaryDirectory(prefix="ylspec-central-") as temporary:
        root = Path(temporary)
        home = root / "gnupg"
        home.mkdir(mode=0o700)
        environment = dict(os.environ, GNUPGHOME=str(home))
        subprocess.run(["gpg", "--batch", "--import"], input=private_key.encode(), env=environment, check=True, capture_output=True)
        keys = subprocess.check_output(["gpg", "--batch", "--with-colons", "--list-secret-keys"], env=environment, text=True)
        fingerprint = next(line.split(":")[9] for line in keys.splitlines() if line.startswith("fpr:"))
        repository = root / "repository"
        with zipfile.ZipFile(os.environ["REGISTRY_ASSET"]) as bundle:
            for member in bundle.infolist():
                path = (repository / member.filename).resolve()
                if not path.is_relative_to(repository.resolve()) or member.is_dir() or path.suffix not in {".jar", ".aar", ".pom", ".module"}:
                    raise ValueError("Unexpected Maven bundle path")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(bundle.read(member))
        originals = sorted(p for p in repository.rglob("*") if p.is_file())
        for path in originals:
            subprocess.run(["gpg", "--batch", "--yes", "--pinentry-mode", "loopback", "--passphrase-fd", "0", "--local-user", fingerprint, "--armor", "--detach-sign", str(path)], input=passphrase.encode(), env=environment, check=True, capture_output=True)
        for path in sorted(p for p in repository.rglob("*") if p.is_file()):
            for algorithm in ("md5", "sha1", "sha256", "sha512"):
                checksum = hashlib.new(algorithm, path.read_bytes()).hexdigest()
                path.with_name(path.name + "." + algorithm).write_text(checksum)
        signed = root / "signed.zip"
        with zipfile.ZipFile(signed, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(p for p in repository.rglob("*") if p.is_file()):
                bundle.write(path, path.relative_to(repository).as_posix())
        boundary = "YLSpec" + uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"bundle\"; filename=\"ylspec-{version}.zip\"\r\nContent-Type: application/zip\r\n\r\n".encode() + signed.read_bytes() + f"\r\n--{boundary}--\r\n".encode())
        headers = {"Authorization": "Bearer " + token, "Content-Type": "multipart/form-data; boundary=" + boundary}
        url = "https://central.sonatype.com/api/v1/publisher/upload?" + urllib.parse.urlencode({"name": "YLSpec " + version, "publishingType": "AUTOMATIC"})
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=120) as response:
            deployment = response.read().decode().strip().strip('"')
        print("Central deployment:", deployment)
        for _ in range(120):
            status_url = "https://central.sonatype.com/api/v1/publisher/status?" + urllib.parse.urlencode({"id": deployment})
            with urllib.request.urlopen(urllib.request.Request(status_url, data=b"", headers={"Authorization": "Bearer " + token}), timeout=60) as response:
                status = json.load(response)
            state = status["deploymentState"]
            print("Central deployment state:", state)
            if state == "PUBLISHED":
                return
            if state == "FAILED":
                raise RuntimeError("Central validation failed: " + json.dumps(status.get("errors", {})))
            time.sleep(10)
        raise TimeoutError("Central publication did not complete within 20 minutes; inspect the recorded deployment")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare-npm", "prepare-maven", "central"])
    args = parser.parse_args()
    if args.command == "central":
        central()
    else:
        prepare("npm" if args.command == "prepare-npm" else "maven")
