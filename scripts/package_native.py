# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Package installed native outputs using stable archive timestamps."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tarfile

version = json.loads(Path("release/release.json").read_text())["version"]
target = sys.argv[1]
epoch = int(subprocess.check_output(["git", "show", "-s", "--format=%ct", "HEAD"]))
name = f"ylspec-{version}-{target}"
Path("dist/native").mkdir(parents=True, exist_ok=True)
with open(f"dist/native/{name}.tar.gz", "wb") as raw:
    with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=epoch) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in sorted(Path("stage").rglob("*")):
                info = archive.gettarinfo(str(path), arcname=f"{name}/{path.relative_to('stage').as_posix()}")
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = epoch
                if path.is_file():
                    with path.open("rb") as stream:
                        archive.addfile(info, stream)
                else:
                    archive.addfile(info)
