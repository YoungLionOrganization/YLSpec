# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Assemble the VS Code package from the verified shared WebAssembly build."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    import cairosvg
    editor = ROOT / "editors/vscode"
    version = json.loads((ROOT / "release/release.json").read_text())["version"]
    info = json.loads((editor / "package.json").read_text(encoding="utf-8"))
    if info["version"] != version:
        raise ValueError("VS Code extension version must match release/release.json")
    for relative in ("src/model.mjs", "src/web.mjs", "wasm/core.mjs", "wasm/core.wasm", "wasm/version.mjs"):
        destination = editor / "engine" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "javascript" / relative, destination)
    for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
        shutil.copyfile(ROOT / name, editor / name)
    vendor = editor / "engine/licenses/tomlc17"
    vendor.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "vendor/tomlc17/LICENSE", vendor / "LICENSE")
    cairosvg.svg2png(url=str(editor / "images/icon.svg"), write_to=str(editor / "images/icon.png"))
    (ROOT / "dist/editor").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
