# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Record reproducible workload details; no pass/fail speed threshold is asserted."""
import json
import platform
import timeit
from pathlib import Path
import ylspec

document = ylspec.Document({"values": list(range(1000)), "name": "benchmark"})
text = ylspec.dumps(document)
frame = ylspec.pack(document)
count = 100
results = {"version": ylspec.__version__, "python": platform.python_version(),
           "platform": platform.platform(), "iterations": count,
           "document_bytes": len(text.encode()), "frame_bytes": len(frame),
           "parse_seconds": timeit.timeit(lambda: ylspec.loads(text), number=count),
           "unpack_seconds": timeit.timeit(lambda: ylspec.unpack(frame), number=count)}
Path("benchmark.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
