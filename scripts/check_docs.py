# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Check local documentation links, source notices, release data, and diagrams."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    generated = ROOT / "build/docs"
    generated.mkdir(parents=True, exist_ok=True)
    diagram_index = 0
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), *sorted((ROOT / "release/notes").glob("*.md"))]:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (path.parent / target).exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
        if text.count("```") % 2:
            errors.append(f"{path.name}: unclosed code fence")
        for diagram in re.findall(r"```mermaid\n(.*?)```", text, re.S):
            (generated / f"diagram-{diagram_index}.mmd").write_text(diagram, encoding="utf-8")
            diagram_index += 1
        if path.name == "README.md":
            snippet = re.search(r"```c\n(.*?)```", text, re.S)
            if not snippet:
                errors.append("README.md: missing executable C quick start")
            else:
                (generated / "readme.c").write_text(snippet.group(1), encoding="utf-8")
    for folder, pattern in [("src", "*.c"), ("include", "*.h"), ("python", "*.py"), ("python", "*.c"), ("tests", "*.c"), ("tests", "*.py"), ("scripts", "*.py"), ("examples", "*.c"), ("examples", "*.py")]:
        for path in (ROOT / folder).rglob(pattern):
            first = path.read_text(encoding="utf-8").splitlines()[0]
            if "Copyright 2026 Cavanşir Qurbanzadə" not in first or "SPDX-License-Identifier: Apache-2.0" not in first:
                errors.append(f"{path}: incomplete original-source notice")
    for path in [ROOT / "LICENSE", ROOT / "NOTICE"]:
        text = path.read_text(encoding="utf-8")
        if "2026" not in text or "Cavanşir Qurbanzadə" not in text:
            errors.append(f"{path.name}: missing copyright metadata")
        if "[yyyy]" in text or "[name of copyright owner]" in text:
            errors.append(f"{path.name}: incomplete copyright template")
    info = json.loads((ROOT / "release/release.json").read_text())
    if not (ROOT / info["notes"]).is_file():
        errors.append("Release notes do not exist")
    if "@PIN" in "".join(p.read_text() for p in (ROOT / ".github/workflows").glob("*.yml")):
        errors.append("Unresolved action pin")
    if not (ROOT / "docs/architecture.mmd").is_file():
        errors.append("Missing architecture diagram source")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Documentation links, release inputs, action pins, and copyright notices passed")


if __name__ == "__main__":
    main()
