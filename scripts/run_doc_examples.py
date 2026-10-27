# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Execute Python documentation snippets against the installed native package."""
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
count = 0
for path in [root / "README.md", *sorted((root / "docs").glob("*.md"))]:
    for snippet in re.findall(r"```python\n(.*?)```", path.read_text(encoding="utf-8"), re.S):
        subprocess.run(["python", "-c", snippet], check=True, cwd=root)
        count += 1
print(f"Executed {count} Python documentation examples")
