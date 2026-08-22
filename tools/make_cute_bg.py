#!/usr/bin/env python3
"""Generate the cute night-sky background for the XLAT 480x272 LCD.

Design notes:
- Overall luminance is kept low so the white UI text stays readable.
- The top-right quadrant (device info text) is kept clean.
- The center (chart area) and bottom (buttons) are kept relatively calm.
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 480, 272
SEED = 42


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient_color(y):
    """Piecewise vertical gradient: dark navy -> indigo -> purple -> mauve."""
    stops = [
        (0.00, (13, 16, 38)),
        (0.45, (28, 32, 74)),
        (0.75, (58, 44, 98)),
        (1.00, (74, 52, 104)),
    ]
    if y <= stops[1][0]:
        return lerp(stops[0][1], stops[1][1], y / stops[1][0])
    if y <= stops[2][0]:
        return lerp(stops[1][1], stops[2][1], (y - stops[1][0]) / (stops[2][0] - stops[1][0]))
    return lerp(stops[2][1], stops[3][1], (y - stops[2][0]) / (stops[3][0] - stops[2][0]))


def draw_stars(base):
    rng = random.Random(SEED)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    palette = [(255, 255, 255), (255, 240, 200), (255, 210, 220), (200, 220, 255)]
    for _ in range(150):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H * 0.85)
        r = rng.choice([1, 1, 1, 2])
        alpha = rng.randint(60, 200)
        col = rng.choice(palette)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*col, alpha))
    # bright four-point twinkle stars
    for _ in range(10):
        x = rng.uniform(20, W - 20)
        y = rng.uniform(8, H * 0.55)
        r = rng.uniform(2.5, 4.5)
        col = rng.choice([(255, 255, 255), (255, 235, 180)])
        d.line((x - r * 2.4, y, x + r * 2.4, y), fill=(*col, 230), width=1)
        d.line((x, y - r * 2.4, x, y + r * 2.4), fill=(*col, 230), width=1)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*col, 235))
    return Image.alpha_composite(base, layer)


def draw_moon(base):
    cx, cy, r = 240, 44, 30
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    dg.ellipse((cx - r * 2.1, cy - r * 2.1, cx + r * 2.1, cy + r * 2.1),
               fill=(255, 235, 190, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(18))

    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(moon)
    dm.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 246, 214, 255))
    # soft shading on the lower-right
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shade)
    ds.ellipse((cx - r + 4, cy - r + 6, cx + r + 6, cy + r + 8), fill=(230, 205, 160, 110))
    shade = shade.filter(ImageFilter.GaussianBlur(6))
    moon = Image.alpha_composite(moon, shade)

    # kawaii face
    df = ImageDraw.Draw(moon)
    eye_d = 5
    for ex in (cx - 11, cx + 11):
        # happy closed eyes (downward arcs)
        df.arc((ex - eye_d, cy - 2, ex + eye_d, cy + 6), start=20, end=160,
               fill=(58, 44, 98, 255), width=2)
    df.arc((cx - 7, cy + 7, cx + 7, cy + 15), start=25, end=155,
           fill=(58, 44, 98, 255), width=2)
    for bx in (cx - 18, cx + 18):
        df.ellipse((bx - 3, cy + 5, bx + 3, cy + 9), fill=(255, 150, 150, 120))

    out = Image.alpha_composite(base, glow)
    out = Image.alpha_composite(out, moon)
    return out


def draw_cloud(base, cx, cy, scale, color, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = 34 * scale
    for ox, oy, rx, ry in [
        (-w * 0.9, 0, w * 0.9, w * 0.55),
        (0, -w * 0.35, w, w * 0.6),
        (w * 0.9, 0, w * 0.9, w * 0.55),
        (0, w * 0.15, w * 1.1, w * 0.5),
    ]:
        d.ellipse((cx + ox - rx, cy + oy - ry, cx + ox + rx, cy + oy + ry),
                  fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(2.5))
    return Image.alpha_composite(base, layer)


def draw_heart(base, x, y, s, color=(255, 170, 190), alpha=180):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # simple heart: two circles + triangle
    r = s
    d.ellipse((x - r, y - r * 0.8, x, y + r * 0.2), fill=(*color, alpha))
    d.ellipse((x, y - r * 0.8, x + r, y + r * 0.2), fill=(*color, alpha))
    d.polygon([(x - r * 0.95, y - r * 0.05), (x + r * 0.95, y - r * 0.05), (x, y + r * 1.15)],
              fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    return Image.alpha_composite(base, layer)


def vignette(base):
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    d.rectangle((0, 0, W, H), fill=255)
    for _ in range(80):
        x = random.Random(SEED + 1).uniform(-80, W + 80)
        y = random.Random(SEED + 2).uniform(-80, H + 80)
        rr = random.Random(SEED + 3).uniform(120, 260)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=240)
    layer = layer.filter(ImageFilter.GaussianBlur(40))
    dark = Image.new("RGB", (W, H), (8, 6, 16))
    return Image.composite(dark, base, layer.point(lambda v: 255 - v))


def main():
    base = Image.new("RGB", (W, H))
    for y in range(H):
        c = gradient_color(y / (H - 1))
        for x in range(W):
            base.putpixel((x, y), c)

    img = base.convert("RGBA")
    img = draw_stars(img)
    img = draw_moon(img)
    img = draw_cloud(img, 62, 70, 1.0, (74, 74, 130), 90)
    img = draw_cloud(img, 330, 78, 0.8, (70, 70, 124), 70)
    img = draw_cloud(img, 415, 232, 0.9, (64, 64, 116), 60)
    img = draw_cloud(img, 58, 238, 0.7, (64, 64, 116), 55)
    img = draw_heart(img, 385, 226, 5, alpha=160)
    img = draw_heart(img, 400, 234, 3, color=(255, 210, 160), alpha=140)
    img = draw_heart(img, 96, 230, 4, color=(200, 180, 255), alpha=130)
    img = vignette(img.convert("RGB"))
    img = img.convert("RGB")
    img.save("img/bg_cute_preview.png")
    print("saved img/bg_cute_preview.png", img.size)


if __name__ == "__main__":
    main()
