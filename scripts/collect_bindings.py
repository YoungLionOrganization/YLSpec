# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Collect only allowlisted adapter binaries from this run's downloaded artifacts."""
import shutil
from bindings import ROOT, NODE_TARGETS, JVM_TARGETS, ANDROID_ABIS

for artifact in (ROOT / "build/downloads").iterdir():
    for source in artifact.rglob("*"):
        if not source.is_file():
            continue
        if artifact.name == "bindings-wasm" and source.name in {"core.mjs", "core.wasm", "version.mjs"}:
            destination = ROOT / "javascript/wasm" / source.name
        elif source.name == "ylspec.node" and source.parent.name in NODE_TARGETS:
            destination = ROOT / "javascript/prebuilds" / source.parent.name / source.name
        elif artifact.name.startswith("bindings-android-") and source.name == "libylspec_jni.so":
            abi = artifact.name.removeprefix("bindings-android-")
            if abi not in ANDROID_ABIS:
                raise ValueError(f"Unexpected Android ABI: {abi}")
            destination = ROOT / "jvm/android/src/main/jni" / abi / source.name
        elif source.name in {"libylspec_jni.so", "libylspec_jni.dylib", "ylspec_jni.dll"} and source.parent.name in JVM_TARGETS:
            destination = ROOT / "jvm/natives/src/main/resources/natives" / source.parent.name / source.name
        else:
            raise ValueError(f"Unexpected binding artifact: {source}")
        if destination.exists():
            raise ValueError(f"Duplicate binding artifact: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
