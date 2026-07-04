#!/usr/bin/env python3
"""
make_icons.py — generate the extension's PNG icons from scratch.

The original icons/ files were JPEG data with a .png extension (and all a single
1008x1008 image), which Chrome will not render as an action icon. This produces
real 8-bit RGBA PNGs at 16/48/128 px: a rounded-square shield in the extension's
accent blue, drawn with 4x supersampling for smooth edges. Pure stdlib (zlib),
no third-party imaging libraries required.

Run:  python make_icons.py
"""

import struct
import zlib
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "extension" / "icons"

SS = 4  # supersampling factor for anti-aliasing

# Palette (matches popup.css: accent #4fc3f7, dark #1e1e1e)
BG = (79, 195, 247)      # accent blue rounded square
SHIELD = (255, 255, 255)  # white shield
CHECK = (11, 61, 92)      # dark navy checkmark


def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def _dist_to_polyline(x, y, pts):
    best = 1e9
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        seg = dx * dx + dy * dy
        t = 0.0 if seg == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / seg))
        px, py = ax + t * dx, ay + t * dy
        best = min(best, ((x - px) ** 2 + (y - py) ** 2) ** 0.5)
    return best


# Geometry in normalized [0,1] coordinates (y grows downward).
SHIELD_POLY = [
    (0.50, 0.12), (0.78, 0.20), (0.78, 0.52),
    (0.68, 0.72), (0.50, 0.88), (0.32, 0.72),
    (0.22, 0.52), (0.22, 0.20),
]
CHECK_LINE = [(0.37, 0.55), (0.46, 0.64), (0.66, 0.40)]
CHECK_WIDTH = 0.05
CORNER_R = 0.20  # rounded-square corner radius (fraction of size)


def _rounded_square_alpha(nx, ny):
    """1.0 inside the rounded square, 0.0 outside (nx, ny in [0,1])."""
    r = CORNER_R
    cx = min(max(nx, r), 1 - r)
    cy = min(max(ny, r), 1 - r)
    d = ((nx - cx) ** 2 + (ny - cy) ** 2) ** 0.5
    return 1.0 if d <= r else 0.0


def render(size):
    R = size * SS
    # supersampled RGBA buffer
    buf = [[(0, 0, 0, 0)] * R for _ in range(R)]
    for py in range(R):
        ny = (py + 0.5) / R
        for px in range(R):
            nx = (px + 0.5) / R
            if _rounded_square_alpha(nx, ny) == 0.0:
                continue
            color = BG
            if _point_in_poly(nx, ny, SHIELD_POLY):
                color = SHIELD
                if _dist_to_polyline(nx, ny, CHECK_LINE) <= CHECK_WIDTH:
                    color = CHECK
            buf[py][px] = (color[0], color[1], color[2], 255)

    # Downsample SSxSS blocks by averaging (box filter -> anti-aliasing).
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # PNG filter type 0 for this scanline
        for x in range(size):
            r = g = b = a = 0
            for dy in range(SS):
                for dx in range(SS):
                    pr, pg, pb, pa = buf[y * SS + dy][x * SS + dx]
                    # premultiply so transparent pixels don't darken edges
                    r += pr * pa
                    g += pg * pa
                    b += pb * pa
                    a += pa
            n = SS * SS
            if a == 0:
                raw += bytes((0, 0, 0, 0))
            else:
                raw += bytes((r // a, g // a, b // a, a // n))
    return bytes(raw)


def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def write_png(path, size):
    raw = render(size)
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(raw, 9))
           + _chunk(b"IEND", b""))
    path.write_bytes(png)
    print(f"  wrote {path.name} ({size}x{size}, {len(png)} bytes)")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating icons in {OUT_DIR} ...")
    for size in (16, 48, 128):
        write_png(OUT_DIR / f"icon{size}.png", size)


if __name__ == "__main__":
    main()
