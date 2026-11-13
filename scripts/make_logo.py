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

Outputs (docs/assets/, for the GitHub README and repository social preview):
  logo-dark.png        320px, transparent: the original light strokes, for dark pages
  logo-light.png       320px, transparent: luminance inverted onto dark slate, for white pages
  social-preview.png   1280x640 on #0d1117 (upload by hand: Settings > Social preview)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cmd" / "dashboard"
DOCS = ROOT / "docs" / "assets"
README_SIZE = 320   # shown at 160px in the README, 2x for hi-dpi
GH_DARK = (13, 17, 23)  # #0d1117
# Light variant: white faces -> dark slate, mid greys stay mid-grey. Linear in luminance,
# so facet ordering is kept (inverted) and the thin grey rings keep >= ~3:1 on white.
LIGHT_MAP = ((255.0, 31.0), (110.0, 125.0))
SLATE_TINT = np.array([-4.0, 0.0, 8.0])  # a cool shift so greys read as slate, not neutral
TAGLINE = "Concentrated-Liquidity Pool Signal Daemon for AI Agents"  # README title
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
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


def light_variant(logo):
    """Same alpha, strokes remapped for a white page."""
    a = np.asarray(logo).astype(np.float64)
    lum = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
    (l1, o1), (l2, o2) = LIGHT_MAP
    target = o2 + (lum - l2) * (o1 - o2) / (l1 - l2)
    target = np.clip(target, o1, 170.0)
    # Scale each pixel toward its target luminance, then tint.
    gain = target / np.maximum(lum, 1.0)
    rgb = np.clip(a[..., :3] * gain[..., None] + SLATE_TINT, 0, 255)
    out = np.dstack([rgb, a[..., 3]]).round().astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def social_preview(logo):
    w, h = 1280, 640
    canvas = Image.new("RGB", (w, h), GH_DARK)
    mark = resize(logo, 400)
    canvas.paste(mark, (110, (h - 400) // 2), mark)
    d = ImageDraw.Draw(canvas)
    title = ImageFont.truetype(FONT_BOLD, 104)
    body = ImageFont.truetype(FONT_REG, 34)
    x = 560
    d.text((x, 205), "Azimuth", font=title, fill=(236, 232, 225))
    d.rectangle((x + 4, 338, x + 84, 342), fill=(217, 154, 78))
    # Wrap the tagline on a word boundary to fit the right column.
    words, lines, cur = TAGLINE.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=body) > w - x - 80 and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    for i, line in enumerate(lines):
        d.text((x + 4, 368 + i * 48), line, font=body, fill=(139, 148, 158))
    return canvas


def save_png(img, path, palette=False):
    if palette:  # 256 colours incl. alpha: visually lossless for flat art, ~3x smaller
        img = img.quantize(colors=256, method=Image.FASTOCTREE, dither=Image.NONE)
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
    DOCS.mkdir(parents=True, exist_ok=True)
    readme = resize(logo, README_SIZE)
    save_png(readme, DOCS / "logo-dark.png", palette=True)
    save_png(light_variant(readme), DOCS / "logo-light.png", palette=True)
    save_png(social_preview(logo), DOCS / "social-preview.png")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
