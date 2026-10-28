# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Build and collect language adapters on GitHub runners; never downloads runtime code on install."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NODE_TARGETS = ["linux-x64-gnu", "linux-arm64-gnu", "linux-x64-musl", "linux-arm64-musl", "win32-x64", "darwin-x64", "darwin-arm64"]
JVM_TARGETS = ["linux-x86_64", "linux-arm64", "linux-x86_64-musl", "linux-arm64-musl", "windows-x86_64", "macos-x86_64", "macos-arm64"]
ANDROID_ABIS = ["armeabi-v7a", "arm64-v8a", "x86", "x86_64"]


def run(*args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def node_headers():
    version = subprocess.check_output(["node", "-p", "process.version"], text=True).strip()
    root = ROOT / "build/node-headers"
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "headers.tar.gz"
    urllib.request.urlretrieve(f"https://nodejs.org/download/release/{version}/node-{version}-headers.tar.gz", archive)
    with tarfile.open(archive) as source:
        source.extractall(root, filter="data")
    include = root / f"node-{version}/include/node"
    library = root / "node.lib"
    if platform.system() == "Windows":
        urllib.request.urlretrieve(f"https://nodejs.org/download/release/{version}/win-x64/node.lib", library)
    return include, library


def copy_binary(build, pattern, destination):
    candidates = [p for p in build.rglob(pattern) if p.is_file() and "CMakeFiles" not in p.parts]
    if len(candidates) != 1:
        raise ValueError(f"Expected exactly one {pattern}, found {candidates}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidates[0], destination)


def build_desktop(node_target, jvm_target, system_headers=False):
    if os.environ.get("YLSPEC_NODE_HEADERS"):
        include, library = Path(os.environ["YLSPEC_NODE_HEADERS"]), Path("unused")
    elif system_headers:
        include, library = Path("/usr/include/node"), Path("unused")
    else:
        include, library = node_headers()
    build = ROOT / "build/bindings"
    run("cmake", "-S", ROOT, "-B", build, "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_TESTING=OFF", "-DYLSPEC_BUILD_CLI=OFF", "-DYLSPEC_BUILD_NODE=ON", "-DYLSPEC_BUILD_JNI=ON",
        f"-DNODE_INCLUDE_DIR={include}", f"-DNODE_LIBRARY={library}", "-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0")
    run("cmake", "--build", build, "--config", "Release", "--parallel", "2")
    copy_binary(build, "ylspec_node.node", ROOT / f"javascript/prebuilds/{node_target}/ylspec.node")
    name = "ylspec_jni.dll" if jvm_target.startswith("windows") else "libylspec_jni.dylib" if jvm_target.startswith("macos") else "libylspec_jni.so"
    copy_binary(build, name, ROOT / f"jvm/natives/src/main/resources/natives/{jvm_target}/{name}")


def prepare_javascript():
    version = json.loads((ROOT / "release/release.json").read_text())["version"]
    info = json.loads((ROOT / "javascript/package.json").read_text(encoding="utf-8"))
    if info["version"] != version:
        raise ValueError("npm version must match release/release.json")
    for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
        shutil.copyfile(ROOT / name, ROOT / "javascript" / name)
    license_path = ROOT / "javascript/licenses/tomlc17"
    license_path.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "vendor/tomlc17/LICENSE", license_path / "LICENSE")
    wasm = ROOT / "javascript/wasm"
    wasm.mkdir(parents=True, exist_ok=True)
    (wasm / "version.mjs").write_text("// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0\nexport const version = " + json.dumps(version) + ";\n", encoding="utf-8")


def package_languages():
    version = json.loads((ROOT / "release/release.json").read_text())["version"]
    for target in NODE_TARGETS:
        if not (ROOT / f"javascript/prebuilds/{target}/ylspec.node").is_file():
            raise ValueError(f"Missing Node target: {target}")
    for target in JVM_TARGETS:
        if not list((ROOT / f"jvm/natives/src/main/resources/natives/{target}").glob("*")):
            raise ValueError(f"Missing JVM target: {target}")
    for abi in ANDROID_ABIS:
        if not (ROOT / f"jvm/android/src/main/jni/{abi}/libylspec_jni.so").is_file():
            raise ValueError(f"Missing Android ABI: {abi}")
    for name in ("core.mjs", "core.wasm"):
        if not (ROOT / "javascript/wasm" / name).is_file():
            raise ValueError(f"Missing WebAssembly asset: {name}")
    prepare_javascript()
    destination = ROOT / "dist/languages"
    destination.mkdir(parents=True, exist_ok=True)
    run("npm", "pack", "--ignore-scripts", "--pack-destination", destination, cwd=ROOT / "javascript")
    repository = ROOT / "jvm/build/maven-repository"
    selected = [p for p in repository.rglob("*") if p.is_file() and p.parent.name == version and p.suffix in {".pom", ".jar", ".aar"}]
    for artifact in ("ylspec", "ylspec-kotlin", "ylspec-natives", "ylspec-android"):
        if not any(p.name == f"{artifact}-{version}.pom" for p in selected):
            raise ValueError(f"Missing Maven publication: {artifact}")
    with zipfile.ZipFile(destination / f"ylspec-jvm-{version}.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(selected):
            bundle.write(path, path.relative_to(repository).as_posix())
            shutil.copyfile(path, destination / path.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["headers", "desktop", "prepare-js", "package"])
    parser.add_argument("--node-target")
    parser.add_argument("--jvm-target")
    parser.add_argument("--system-headers", action="store_true")
    args = parser.parse_args()
    if args.command == "headers":
        include, library = node_headers()
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write(f"include={include}\nlibrary={library}\n")
    elif args.command == "desktop":
        build_desktop(args.node_target, args.jvm_target, args.system_headers)
    elif args.command == "prepare-js":
        prepare_javascript()
    else:
        package_languages()


if __name__ == "__main__":
    main()
