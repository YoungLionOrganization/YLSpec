# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Validate release inputs, stage artifacts, and publish without replacing bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def metadata():
    info = json.loads((ROOT / "release/release.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"0\.[0-9]+\.[0-9]+", info["version"]):
        raise ValueError("Release version must have the form 0.MINOR.PATCH")
    notes = (ROOT / info["notes"]).resolve()
    if not notes.is_relative_to(ROOT / "release/notes") or not notes.is_file():
        raise ValueError("Notes must reference an existing release/notes file")
    if not isinstance(info["prerelease"], bool) or not info["title"].strip():
        raise ValueError("Invalid release title or prerelease flag")
    return info


def digest(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True, encoding="utf-8")


def stage(source, destination, sha):
    import shutil
    info = metadata()
    expected = json.loads((ROOT / "release/assets.json").read_text())
    destination.mkdir(parents=True, exist_ok=True)
    files = list(source.rglob("*.whl")) + list(source.rglob("*.tar.gz"))
    names = set()
    for path in files:
        if path.name in names:
            raise ValueError(f"Duplicate artifact name: {path.name}")
        names.add(path.name)
        shutil.copyfile(path, destination / path.name)
    for target in expected["native_targets"]:
        name = expected["native_pattern"].format(version=info["version"], target=target)
        if name not in names:
            raise ValueError(f"Missing native artifact: {name}")
    wheels = list(destination.glob("*.whl"))
    for family in expected["required_wheel_platforms"]:
        # Match full architecture suffix while allowing manylinux compatibility tags.
        if not any(family == "win_amd64" and "win_amd64" in p.name or
                   family.startswith("macosx_") and "macosx" in p.name and family[7:] in p.name or
                   family.startswith("manylinux_") and "manylinux" in p.name and family[10:] in p.name or
                   family.startswith("musllinux_") and "musllinux" in p.name and family[10:] in p.name for p in wheels):
            raise ValueError(f"Missing wheel platform: {family}")
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
            text = archive.read(name).decode()
            if f"\nVersion: {info['version']}\n" not in text or "\nName: ylspec\n" not in text:
                raise ValueError(f"Wheel metadata mismatch: {wheel.name}")
    sdist = destination / expected["source_pattern"].format(version=info["version"])
    if not sdist.is_file():
        raise ValueError("Missing source distribution")
    with tarfile.open(sdist) as archive:
        member = next(m for m in archive.getmembers() if m.name.endswith("/PKG-INFO") and m.name.count("/") == 1)
        if f"\nVersion: {info['version']}\n" not in archive.extractfile(member).read().decode():
            raise ValueError("Source distribution version mismatch")
    manifest = {"version": info["version"], "commit": sha,
                "assets": {p.name: digest(p) for p in sorted(destination.iterdir()) if p.is_file()}}
    (destination / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (destination / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(destination.iterdir()) if p.is_file() and p.name != "SHA256SUMS"))


def pypi_pending(staged, pending):
    """Only skip an existing filename after verifying PyPI's reported SHA-256."""
    import shutil
    info = metadata()
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/ylspec/{info['version']}/json", timeout=30) as response:
            published = {x["filename"]: x["digests"]["sha256"] for x in json.load(response)["urls"]}
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        published = {}
    pending.mkdir(parents=True, exist_ok=True)
    for path in staged.iterdir():
        if path.suffix == ".whl" or path.name == f"ylspec-{info['version']}.tar.gz":
            if path.name in published:
                if published[path.name] != digest(path):
                    raise ValueError(f"Published bytes differ: {path.name}; use a new version")
            else:
                shutil.copyfile(path, pending / path.name)
    return any(pending.iterdir())


def draft(staged, sha):
    info = metadata()
    tag = "v" + info["version"]
    repo = os.environ["GITHUB_REPOSITORY"]
    try:
        ref = json.loads(gh("api", f"repos/{repo}/git/ref/tags/{tag}"))
    except subprocess.CalledProcessError:
        ref = None
    if ref and (ref["object"]["type"] != "commit" or ref["object"]["sha"] != sha):
        raise ValueError("Existing release tag does not point to this commit")
    try:
        release = json.loads(gh("api", f"repos/{repo}/releases/tags/{tag}"))
    except subprocess.CalledProcessError:
        release = None
    if release and not release["draft"]:
        raise ValueError("Release is already public; create a new version")
    if not release:
        args = ["release", "create", tag, "--repo", repo, "--target", sha, "--draft", "--title", info["title"], "--notes-file", str(ROOT / info["notes"])]
        if info["prerelease"]:
            args.append("--prerelease")
        gh(*args)
        release = json.loads(gh("api", f"repos/{repo}/releases/tags/{tag}"))
    assets = {x["name"]: x for x in release["assets"]}
    for path in sorted(staged.iterdir()):
        if path.name in assets:
            # API asset digests are preferred; download existing bytes if unavailable.
            asset = assets[path.name]
            known = asset.get("digest")
            if known:
                if known != "sha256:" + digest(path):
                    raise ValueError(f"Existing asset differs: {path.name}")
            else:
                import tempfile
                with tempfile.TemporaryDirectory() as folder:
                    gh("release", "download", tag, "--repo", repo, "--pattern", path.name, "--dir", folder)
                    if digest(Path(folder) / path.name) != digest(path):
                        raise ValueError(f"Existing asset differs: {path.name}")
        else:
            gh("release", "upload", tag, str(path), "--repo", repo)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["metadata", "stage", "pending", "draft", "finalize"])
    parser.add_argument("--source", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, default=Path("dist/release"))
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
    args = parser.parse_args()
    if args.command == "metadata":
        print(json.dumps(metadata()))
    elif args.command == "stage":
        stage(args.source, args.output, args.sha)
    elif args.command == "pending":
        result = pypi_pending(args.source, args.output)
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write(f"has_files={str(result).lower()}\n")
    elif args.command == "draft":
        draft(args.source, args.sha)
    else:
        gh("release", "edit", "v" + metadata()["version"], "--repo", os.environ["GITHUB_REPOSITORY"], "--draft=false")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Release failed: {error}", file=sys.stderr)
        raise
