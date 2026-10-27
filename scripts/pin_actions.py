# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Resolve reviewed action tags to immutable commits using authenticated gh."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = ["actions/checkout", "actions/setup-python", "actions/upload-artifact",
           "actions/download-artifact", "actions/setup-go", "actions/setup-node",
           "pypa/cibuildwheel", "pypa/gh-action-pypi-publish"]


def api(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint], text=True, encoding="utf-8"))


def main():
    pin_file = ROOT / ".github/action-pins.json"
    pins = json.loads(pin_file.read_text()) if pin_file.exists() and "--refresh" not in sys.argv else {}
    for action in ACTIONS:
        if action not in pins:
            tag = "release/v1" if action.endswith("gh-action-pypi-publish") else api(f"repos/{action}/releases/latest")["tag_name"]
            commit = api(f"repos/{action}/commits/{tag}")["sha"]
            pins[action] = {"tag": tag, "sha": commit}
        print(f"{action}: {pins[action]['tag']} -> {pins[action]['sha']}")
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        for action, pin in pins.items():
            text = re.sub(rf"uses: {re.escape(action)}@PIN(?:\s*#[^\n]*)?", f"uses: {action}@{pin['sha']} # {pin['tag']}", text)
        path.write_text(text, encoding="utf-8", newline="\n")
    (ROOT / ".github/action-pins.json").write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
