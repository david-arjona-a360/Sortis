"""
Generate assets/blueprint.ico from src/theme/blueprint.png.

Builds a multi-resolution ICO (16..256 px, PNG-compressed entries) using
PySide6 QImage so no extra dependency is required. Run from the project root:

    .venv/Scripts/python.exe scripts/make_icon.py
"""

import os
import struct
import sys

from PySide6.QtCore import QBuffer, Qt
from PySide6.QtGui import QImage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "src", "theme", "blueprint.png")
TARGET = os.path.join(ROOT, "assets", "blueprint.ico")
SIZES = (16, 24, 32, 48, 64, 128, 256)


def _encode_png(image, size):
    scaled = image.scaled(
        size, size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    buf = QBuffer()
    buf.open(QBuffer.OpenModeFlag.WriteOnly)
    scaled.save(buf, "PNG")
    buf.close()
    return bytes(buf.data())


def _build_ico(blobs, sizes):
    count = len(blobs)
    header = struct.pack("<HHH", 0, 1, count)
    entries = b""
    offset = 6 + 16 * count
    for blob, size in zip(blobs, sizes):
        dim = 0 if size >= 256 else size
        entries += struct.pack(
            "<BBBBHHII", dim, dim, 0, 0, 1, 32, len(blob), offset
        )
        offset += len(blob)
    return header + entries + b"".join(blobs)


def main():
    if not os.path.exists(SOURCE):
        print(f"ERROR: source not found: {SOURCE}")
        sys.exit(1)
    image = QImage(SOURCE)
    if image.isNull():
        print(f"ERROR: could not load {SOURCE}")
        sys.exit(1)
    blobs = [_encode_png(image, size) for size in SIZES]
    ico = _build_ico(blobs, SIZES)
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    with open(TARGET, "wb") as fh:
        fh.write(ico)
    print(f"Generated {TARGET}")
    print(f"  source: {image.width()}x{image.height()} {image.format().name}")
    print(f"  entries: {', '.join(str(s) for s in SIZES)}")
    print(f"  size: {len(ico)} bytes")


if __name__ == "__main__":
    main()
