#!/usr/bin/env python3
"""Build the dashboard logo assets from the operator's source artwork.

    python3 -m venv /tmp/logo-venv && /tmp/logo-venv/bin/pip install pillow numpy
    /tmp/logo-venv/bin/python scripts/make_logo.py /path/to/azimuth-logo.jpg

Pillow and numpy are build-time tools only; the generated PNG/ICO files are
committed, so neither is a dependency of the repo or the dashboard.

The art is light on a near-black background. Alpha is a smooth ramp of
luminance (no hard threshold), and the colour is un-composited from the
background so anti-aliased edges carry no dark halo. Resizing is done on
premultiplied pixels for the same reason.

Outputs (cmd/dashboard/):
  logo.png        512px, transparent
  logo-64.png     64px, transparent (header; shown at 32px, 2x for hi-dpi)
  favicon-32.png  32px on a dark rounded badge (browser tabs may be light)
  favicon.ico     16/32/48 on the same badge
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "cmd" / "dashboard"
LO, HI = 22.0, 90.0   # luminance ramp: <=LO fully transparent, >=HI fully opaque
PAD = 0.04            # padding per side, fraction of the content box
BADGE = (22, 24, 27, 255)  # #16181b, the same dark as the legacy mark.svg


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def extract(src):
    rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float64)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    # Background level from the image border (JPEG leaves it a flat ~16).
    border = np.concatenate([lum[:40].ravel(), lum[-40:].ravel(), lum[:, :40].ravel(), lum[:, -40:].ravel()])
    bg = float(np.median(border))
    alpha = smoothstep((lum - LO) / (HI - LO))
    a3 = alpha[..., None]
    # Un-composite: pixel = a*c + (1-a)*bg  ->  c = (pixel - (1-a)*bg) / a
    color = np.where(a3 > 1e-3, (rgb - (1 - a3) * bg) / np.maximum(a3, 1e-3), 0.0)
    color = np.clip(color, 0, 255)
    out = np.dstack([color, alpha * 255.0]).round().astype(np.uint8)
    return Image.fromarray(out, "RGBA"), alpha


def trim_square(img, alpha):
    ys, xs = np.where(alpha > 0.5)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    side = int(round(max(x1 - x0, y1 - y0) * (1 + 2 * PAD)))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    left, top = int(round(cx - side / 2)), int(round(cy - side / 2))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, (-left, -top))
    return canvas


def resize(img, size):
    # Premultiplied resize: no dark fringe where alpha falls off.
    return img.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA")


def badge(logo, size):
    scale = 8  # draw the rounded rect supersampled, then reduce
    big = size * scale
    base = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(base).rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 0.18, fill=BADGE)
    base = base.resize((size, size), Image.LANCZOS)
    inner = int(round(size * 0.86))
    mark = resize(logo, inner)
    base.alpha_composite(mark, ((size - inner) // 2, (size - inner) // 2))
    return base


def save_png(img, path):
    img.save(path, optimize=True)
    print(f"{path.name}: {path.stat().st_size} bytes")


def main(src):
    img, alpha = extract(src)
    logo = trim_square(img, alpha)
    save_png(resize(logo, 512), OUT / "logo.png")
    save_png(resize(logo, 64), OUT / "logo-64.png")
    save_png(badge(logo, 32), OUT / "favicon-32.png")
    badge(logo, 48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"favicon.ico: {(OUT / 'favicon.ico').stat().st_size} bytes")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
