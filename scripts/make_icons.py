#!/usr/bin/env python3
"""
make_icons.py — generate the extension's PNG icons (16/48/128).

Two modes:

  1. From a source image (preferred — use your real logo):
         python make_icons.py --source path/to/logo.png
     The source must be a PNG (8-bit, non-interlaced — a normal export).
     By default the emblem is auto-cropped to a centered square and the
     bottom text band is dropped so the icon stays legible at 16px. Override
     the crop with --crop LEFT,TOP,RIGHT,BOTTOM (fractions 0..1), or disable
     it with --no-crop.

  2. Synthetic fallback (no source): draws a simple shield glyph.
         python make_icons.py --synthetic

If no flag is given and extension/icons/source.png exists, it is used
automatically; otherwise the synthetic icon is drawn.

Pure standard library (zlib only) — no Pillow/ImageMagick required, so it runs
anywhere Python does.
"""

import argparse
import struct
import sys
import zlib
from pathlib import Path

ICONS_DIR = Path(__file__).parent.parent / "extension" / "icons"
SIZES = (16, 48, 128)


# ---------------------------------------------------------------------------
# Minimal PNG codec (8-bit, non-interlaced)
# ---------------------------------------------------------------------------

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def load_png(path):
    """Return (width, height, rgba_bytearray) for an 8-bit non-interlaced PNG."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG (got magic {data[:8]!r}). "
                         f"Export/save the logo as PNG and retry.")
    pos = 8
    width = height = bitdepth = colortype = None
    idat = bytearray()
    palette = None
    trns = None
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            width, height, bitdepth, colortype, _comp, _filt, interlace = \
                struct.unpack(">IIBBBBB", chunk)
            if interlace != 0:
                raise ValueError("Interlaced PNGs are not supported; re-export "
                                 "without interlacing.")
            if bitdepth != 8:
                raise ValueError(f"Only 8-bit PNGs are supported (got {bitdepth}-bit).")
        elif tag == b"PLTE":
            palette = chunk
        elif tag == b"tRNS":
            trns = chunk
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    stride = width * channels
    raw = zlib.decompress(bytes(idat))

    # Reverse the per-scanline filters.
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    bpp = channels
    for _y in range(height):
        ftype = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if ftype == 1:      # Sub
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:    # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:    # Average
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:    # Paeth
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(a, prev[i], c)) & 0xFF
        elif ftype != 0:
            raise ValueError(f"Unknown PNG filter type {ftype}")
        out += line
        prev = line

    # Expand to RGBA.
    rgba = bytearray(width * height * 4)
    for i in range(width * height):
        if colortype == 6:      # RGBA
            rgba[i * 4:i * 4 + 4] = out[i * 4:i * 4 + 4]
        elif colortype == 2:    # RGB
            rgba[i * 4:i * 4 + 3] = out[i * 3:i * 3 + 3]
            rgba[i * 4 + 3] = 255
        elif colortype == 0:    # grayscale
            g = out[i]
            rgba[i * 4:i * 4 + 4] = bytes((g, g, g, 255))
        elif colortype == 4:    # gray + alpha
            g, a = out[i * 2], out[i * 2 + 1]
            rgba[i * 4:i * 4 + 4] = bytes((g, g, g, a))
        elif colortype == 3:    # palette
            idx = out[i]
            rgba[i * 4:i * 4 + 3] = palette[idx * 3:idx * 3 + 3]
            rgba[i * 4 + 3] = trns[idx] if (trns and idx < len(trns)) else 255
    return width, height, rgba


def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def save_png(path, size, rgba):
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type 0
        raw += rgba[y * size * 4:(y + 1) * size * 4]
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    Path(path).write_bytes(png)
    print(f"  wrote {Path(path).name} ({size}x{size}, {len(png)} bytes)")


# ---------------------------------------------------------------------------
# Crop + high-quality box downscale
# ---------------------------------------------------------------------------

def _pixel(rgba, w, x, y):
    o = (y * w + x) * 4
    return rgba[o], rgba[o + 1], rgba[o + 2], rgba[o + 3]


def crop(rgba, w, h, box):
    l, t, r, b = box
    x0, y0 = max(0, int(l * w)), max(0, int(t * h))
    x1, y1 = min(w, int(r * w)), min(h, int(b * h))
    cw, ch = x1 - x0, y1 - y0
    out = bytearray(cw * ch * 4)
    for y in range(ch):
        src = ((y0 + y) * w + x0) * 4
        out[y * cw * 4:(y + 1) * cw * 4] = rgba[src:src + cw * 4]
    return cw, ch, out


def auto_emblem_box(rgba, w, h, dark=40):
    """Bounding box (fractions) of the non-dark artwork, then a top-anchored
    square so a bottom text band is dropped and the emblem stays centered."""
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            rr, gg, bb, aa = _pixel(rgba, w, x, y)
            if aa > 10 and (rr > dark or gg > dark or bb > dark):
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
    if maxx <= minx or maxy <= miny:
        return (0.0, 0.0, 1.0, 1.0)
    bw = maxx - minx
    # Square, anchored at the artwork's top, width = artwork width. This keeps
    # the emblem and clips a wide/short text band beneath it.
    side = min(bw, h - miny)
    cx = (minx + maxx) / 2
    x0 = max(0, min(w - side, int(cx - side / 2)))
    y0 = miny
    return (x0 / w, y0 / h, (x0 + side) / w, (y0 + side) / h)


def downscale(rgba, w, h, size):
    """Box-filter downscale to size×size RGBA (premultiplied for clean edges)."""
    out = bytearray(size * size * 4)
    for oy in range(size):
        sy0, sy1 = oy * h // size, max(oy * h // size + 1, (oy + 1) * h // size)
        for ox in range(size):
            sx0, sx1 = ox * w // size, max(ox * w // size + 1, (ox + 1) * w // size)
            r = g = b = a = n = 0
            for sy in range(sy0, sy1):
                base = sy * w
                for sx in range(sx0, sx1):
                    o = (base + sx) * 4
                    pa = rgba[o + 3]
                    r += rgba[o] * pa
                    g += rgba[o + 1] * pa
                    b += rgba[o + 2] * pa
                    a += pa
                    n += 1
            o = (oy * size + ox) * 4
            if a == 0:
                out[o:o + 4] = bytes(4)
            else:
                out[o:o + 4] = bytes((r // a, g // a, b // a, a // n))
    return out


def make_square(rgba, w, h):
    """Pad the shorter axis with transparency to make the image square."""
    if w == h:
        return w, h, rgba
    s = max(w, h)
    out = bytearray(s * s * 4)
    ox, oy = (s - w) // 2, (s - h) // 2
    for y in range(h):
        dst = ((oy + y) * s + ox) * 4
        out[dst:dst + w * 4] = rgba[y * w * 4:(y + 1) * w * 4]
    return s, s, out


# ---------------------------------------------------------------------------
# Synthetic fallback shield (used when no source image is provided)
# ---------------------------------------------------------------------------

def synthetic(size):
    SS = 4
    BG, SHIELD, CHECK = (79, 195, 247), (255, 255, 255), (11, 61, 92)
    SHIELD_POLY = [(0.50, 0.12), (0.78, 0.20), (0.78, 0.52), (0.68, 0.72),
                   (0.50, 0.88), (0.32, 0.72), (0.22, 0.52), (0.22, 0.20)]
    CHECK_LINE = [(0.37, 0.55), (0.46, 0.64), (0.66, 0.40)]

    def in_poly(x, y, poly):
        inside, j = False, len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]; xj, yj = poly[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside

    def dist_line(x, y, pts):
        best = 1e9
        for i in range(len(pts) - 1):
            ax, ay = pts[i]; bx, by = pts[i + 1]
            dx, dy = bx - ax, by - ay
            seg = dx * dx + dy * dy
            t = 0 if seg == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / seg))
            best = min(best, ((x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2) ** 0.5)
        return best

    R = size * SS
    src = bytearray(R * R * 4)
    r = 0.20
    for py in range(R):
        ny = (py + 0.5) / R
        for px in range(R):
            nx = (px + 0.5) / R
            cx, cy = min(max(nx, r), 1 - r), min(max(ny, r), 1 - r)
            if ((nx - cx) ** 2 + (ny - cy) ** 2) ** 0.5 > r:
                continue
            color = BG
            if in_poly(nx, ny, SHIELD_POLY):
                color = CHECK if dist_line(nx, ny, CHECK_LINE) <= 0.05 else SHIELD
            o = (py * R + px) * 4
            src[o:o + 4] = bytes((*color, 255))
    return downscale(src, R, R, size)


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate extension icons.")
    ap.add_argument("--source", help="Source logo PNG to downscale into icons.")
    ap.add_argument("--crop", help="Crop box as LEFT,TOP,RIGHT,BOTTOM fractions (0..1).")
    ap.add_argument("--no-crop", action="store_true", help="Do not auto-crop the emblem.")
    ap.add_argument("--synthetic", action="store_true", help="Draw the synthetic shield.")
    args = ap.parse_args()

    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    source = args.source
    if not source and not args.synthetic:
        default_src = ICONS_DIR / "source.png"
        if default_src.exists():
            source = str(default_src)

    if source and not args.synthetic:
        print(f"Building icons from {source} ...")
        w, h, rgba = load_png(source)
        if args.crop:
            box = tuple(float(v) for v in args.crop.split(","))
            w, h, rgba = crop(rgba, w, h, box)
        elif not args.no_crop:
            box = auto_emblem_box(rgba, w, h)
            print(f"  auto-crop box (fractions): "
                  f"{tuple(round(v, 3) for v in box)}")
            w, h, rgba = crop(rgba, w, h, box)
        w, h, rgba = make_square(rgba, w, h)
        for size in SIZES:
            save_png(ICONS_DIR / f"icon{size}.png", size, downscale(rgba, w, h, size))
    else:
        print("Drawing synthetic shield icons ...")
        for size in SIZES:
            save_png(ICONS_DIR / f"icon{size}.png", size, synthetic(size))


if __name__ == "__main__":
    main()
