"""news-image-20261125: write the day's news image to /output/entry.png.

The image (entry.png, shipped beside this file) is a newspaper front page
summing up the world news of Wednesday 25 November 2026: the Trump
administration poised to unveil new tariffs after its Section 301 probe
into excess factory capacity (Asian markets tumble), Shanghai party chief
Chen Jining under investigation, a US jury convicting Huawei of stealing
trade secrets, a second Houthi strike on Riyadh's tallest tower, and
Nvidia's Jensen Huang apologising to staff as the comeback rally fades —
plus Shenzhou-24, the Colombia supermarket hostages and the Thanksgiving
turkey pardon.

Standard library only. No network. Deterministic: the output bytes are an
exact copy of the shipped image, so two runs write identical bytes.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import sys

IMAGE_NAME = "entry.png"
MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IEND_TRAILER = b"IEND\xaeB`\x82"


def _image_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, IMAGE_NAME)


def _read_and_validate(path):
    """Read the shipped image and check the competition's gate rules."""
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{IMAGE_NAME} is {len(data)} bytes, over the 1 MiB cap")
    if data[:8] != PNG_SIGNATURE:
        raise SystemExit(f"{IMAGE_NAME} is not a PNG file")
    width, height = struct.unpack(">II", data[16:24])
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise SystemExit(f"{IMAGE_NAME} is {width}x{height}, over 1024x1024")
    if width == 0 or height == 0:
        raise SystemExit(f"{IMAGE_NAME} has a zero dimension")
    if not data.endswith(IEND_TRAILER):
        raise SystemExit(f"{IMAGE_NAME} is truncated: no IEND trailer")
    return data, width, height


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data, width, height = _read_and_validate(_image_path())
    out_path = os.path.join(out_dir, "entry.png")
    with open(out_path, "wb") as fh:
        fh.write(data)
    print(f"wrote {out_path} ({len(data)} bytes, {width}x{height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
