# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Run with: python examples/basic.py after installing the package."""
import io
import ylspec

document = ylspec.Document({"name": "Example", "enabled": True})
document.validate()
frame = ylspec.pack(document)
prefix = b"host-defined prefix"
carrier = io.BytesIO(prefix + frame + b"unrelated payload")
restored = ylspec.read_at(carrier, offset=len(prefix), available=len(frame))
assert restored.data == document.data
assert ylspec.unpack(prefix + frame, offset=len(prefix)).data == document.data
print(ylspec.dumps(restored))
