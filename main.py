#!/usr/bin/env python3
"""Ship the bundled news image to the grader's output folder.

The entry image lives next to this script as ``entry.png``.  This program
walks the file's PNG chunk stream to prove it is a complete image inside
the competition's limits, then places an exact copy at
``$MAKEFUN_OUTPUT_DIR/entry.png`` (``/output`` when the variable is
unset) and reports what it delivered.  Only the Python standard library
is used.
"""

from __future__ import annotations

import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576
MAX_EDGE = 1024


class PictureProblem(Exception):
    """Raised when the bundled image breaks a competition rule."""


def _u32be(raw: bytes) -> int:
    return struct.unpack(">I", raw)[0]


def _read_all(blob_path: Path) -> bytes:
    try:
        return blob_path.read_bytes()
    except OSError as exc:
        raise PictureProblem(f"cannot read {blob_path}: {exc}") from exc


def _scan_chunks(payload: bytes) -> dict:
    """Walk the PNG chunk stream; return width/height once IEND is seen."""
    if payload[: len(PNG_MAGIC)] != PNG_MAGIC:
        raise PictureProblem("first bytes are not the PNG signature")
    cursor = len(PNG_MAGIC)
    seen_ihdr = False
    seen_iend = False
    width = height = 0
    while cursor < len(payload):
        if cursor + 8 > len(payload):
            raise PictureProblem("chunk header runs past end of file")
        body_len = _u32be(payload[cursor : cursor + 4])
        label = payload[cursor + 4 : cursor + 8]
        body_start = cursor + 8
        body_end = body_start + body_len
        if body_end + 4 > len(payload):
            raise PictureProblem(f"chunk {label!r} is truncated")
        stored_crc = _u32be(payload[body_end : body_end + 4])
        actual_crc = zlib.crc32(label + payload[body_start:body_end]) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise PictureProblem(f"chunk {label!r} fails its CRC check")
        if label == b"IHDR":
            if seen_ihdr or body_len != 13:
                raise PictureProblem("bad IHDR chunk")
            width, height = struct.unpack(">II", payload[body_start : body_start + 8])
            seen_ihdr = True
        elif label == b"IEND":
            if body_len != 0:
                raise PictureProblem("IEND chunk must be empty")
            seen_iend = True
            if body_end + 4 != len(payload):
                raise PictureProblem("bytes after the IEND trailer")
            break
        cursor = body_end + 4
    if not seen_ihdr:
        raise PictureProblem("no IHDR chunk found")
    if not seen_iend:
        raise PictureProblem("missing IEND trailer")
    return {"width": width, "height": height}


def _check_limits(payload: bytes, facts: dict) -> None:
    if len(payload) > MAX_BYTES:
        raise PictureProblem(
            f"image is {len(payload)} bytes, over the {MAX_BYTES} byte cap"
        )
    if facts["width"] > MAX_EDGE or facts["height"] > MAX_EDGE:
        raise PictureProblem(
            f"image is {facts['width']}x{facts['height']}, "
            f"over the {MAX_EDGE}x{MAX_EDGE} cap"
        )
    if facts["width"] == 0 or facts["height"] == 0:
        raise PictureProblem("image has a zero dimension")


def _deliver(payload: bytes, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / "entry.png"
    destination.write_bytes(payload)
    reread = _read_all(destination)
    if reread != payload:
        raise PictureProblem(f"delivered copy at {destination} differs from source")
    return destination


def _fingerprint(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    here = Path(__file__).resolve().parent
    source = here / "entry.png"
    payload = _read_all(source)
    facts = _scan_chunks(payload)
    _check_limits(payload, facts)
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    destination = _deliver(payload, out_dir)
    print(
        f"wrote {destination} "
        f"({len(payload)} bytes, {facts['width']}x{facts['height']}, "
        f"sha256 {_fingerprint(payload)})"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PictureProblem as problem:
        print(f"error: {problem}", file=sys.stderr)
        raise SystemExit(1)
