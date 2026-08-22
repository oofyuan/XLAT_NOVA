#!/usr/bin/env python3
"""Generate a pink anime-esports background for the XLAT 480x272 LCD.

Theme: 粉色二次元电竞少女
- Pink night gradient (kept dark enough for white UI text).
- Crescent-free full moon with a kawaii face wearing esports headphones.
- Small anime-girl silhouette (twin tails + headphones) sitting on the moon.
- Stars, hearts and a tiny game controller.
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 480, 272
SEED = 42


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient_color(y):
    """Vertical pink gradient: deep magenta-plum -> rose -> soft violet."""
    stops = [
        (0.00, (52, 12, 44)),   # deep magenta-plum
        (0.45, (74, 20, 58)),   # rose-magenta
        (0.75, (96, 32, 72)),   # raspberry
        (1.00, (110, 44, 88)),  # soft plum-violet
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
    palette = [(255, 255, 255), (255, 220, 235), (255, 190, 215), (230, 200, 255)]
    for _ in range(160):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H * 0.82)
        r = rng.choice([1, 1, 1, 2])
        alpha = rng.randint(60, 200)
        col = rng.choice(palette)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*col, alpha))
    for _ in range(12):
        x = rng.uniform(20, W - 20)
        y = rng.uniform(8, H * 0.55)
        r = rng.uniform(2.5, 4.5)
        col = rng.choice([(255, 255, 255), (255, 200, 220), (255, 170, 200)])
        d.line((x - r * 2.4, y, x + r * 2.4, y), fill=(*col, 230), width=1)
        d.line((x, y - r * 2.4, x, y + r * 2.4), fill=(*col, 230), width=1)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*col, 235))
    return Image.alpha_composite(base, layer)


def draw_moon(base, cx, cy, r):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    dg.ellipse((cx - r * 2.1, cy - r * 2.1, cx + r * 2.1, cy + r * 2.1),
               fill=(255, 210, 225, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(18))

    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(moon)
    dm.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 236, 242, 255))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shade)
    ds.ellipse((cx - r + 4, cy - r + 6, cx + r + 6, cy + r + 8), fill=(250, 190, 210, 120))
    shade = shade.filter(ImageFilter.GaussianBlur(6))
    moon = Image.alpha_composite(moon, shade)

    # kawaii face
    df = ImageDraw.Draw(moon)
    eye_d = 5
    for ex in (cx - 11, cx + 11):
        df.arc((ex - eye_d, cy - 2, ex + eye_d, cy + 6), start=20, end=160,
               fill=(120, 40, 80, 255), width=2)
    df.arc((cx - 7, cy + 7, cx + 7, cy + 15), start=25, end=155,
           fill=(120, 40, 80, 255), width=2)
    for bx in (cx - 18, cx + 18):
        df.ellipse((bx - 3, cy + 5, bx + 3, cy + 9), fill=(255, 140, 160, 130))

    # esports headphones on the moon
    hp = ImageDraw.Draw(moon)
    hp.arc((cx - r * 0.92, cy - r * 0.92, cx + r * 0.92, cy + r * 0.92),
           start=200, end=340, fill=(70, 20, 55, 255), width=4)
    for ex in (cx - r * 0.88, cx + r * 0.88):
        hp.rounded_rectangle(
            (ex - 5, cy - r * 0.72, ex + 5, cy + r * 0.55),
            radius=3, fill=(70, 20, 55, 255))
        hp.rounded_rectangle(
            (ex - 3, cy - r * 0.70, ex + 3, cy - r * 0.55),
            radius=2, fill=(255, 150, 190, 255))

    out = Image.alpha_composite(base, glow)
    out = Image.alpha_composite(out, moon)
    return out


def draw_girl(base, gx, gy, s=1.0):
    """Tiny anime-girl silhouette with pink twin tails, sitting on the moon."""
    col = (60, 16, 46)
    tail = (255, 170, 200)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # twin tails (rotated ellipses on each side)
    for side in (-1, 1):
        d.ellipse((gx + side * 4 * s - 3.2 * s, gy - 13 * s,
                   gx + side * 4 * s + 3.2 * s, gy + 3 * s), fill=tail)
        d.ellipse((gx + side * 4 * s - 1.5 * s, gy - 10 * s,
                   gx + side * 4 * s + 1.5 * s, gy - 4 * s), fill=(255, 220, 235))

    # body (sitting): skirt + torso
    d.polygon([(gx - 5 * s, gy - 6 * s), (gx + 5 * s, gy - 6 * s),
               (gx + 7 * s, gy + 6 * s), (gx - 7 * s, gy + 6 * s)], fill=col)
    d.rounded_rectangle((gx - 4 * s, gy - 9 * s, gx + 4 * s, gy - 3 * s),
                        radius=2 * s, fill=col)

    # head
    d.ellipse((gx - 5.5 * s, gy - 17 * s, gx + 5.5 * s, gy - 6 * s), fill=col)
    # hair highlight
    d.ellipse((gx - 4 * s, gy - 16 * s, gx - 1 * s, gy - 12 * s),
              fill=(255, 150, 190, 200))

    # esports headphones on the girl
    d.arc((gx - 6 * s, gy - 18 * s, gx + 6 * s, gy - 6 * s),
          start=180, end=360, fill=(30, 8, 24), width=2)
    for side in (-1, 1):
        ex = gx + side * 5.5 * s
        d.rounded_rectangle((ex - 1.8 * s, gy - 15 * s, ex + 1.8 * s, gy - 9 * s),
                            radius=1 * s, fill=(30, 8, 24))
    return Image.alpha_composite(base, layer)


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


def draw_heart(base, x, y, s, color=(255, 150, 185), alpha=170):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = s
    d.ellipse((x - r, y - r * 0.8, x, y + r * 0.2), fill=(*color, alpha))
    d.ellipse((x, y - r * 0.8, x + r, y + r * 0.2), fill=(*color, alpha))
    d.polygon([(x - r * 0.95, y - r * 0.05), (x + r * 0.95, y - r * 0.05), (x, y + r * 1.15)],
              fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    return Image.alpha_composite(base, layer)


def draw_controller(base, x, y, s=1.0):
    col = (70, 20, 58)
    acc = (255, 180, 205)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = 16 * s, 9 * s
    d.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2),
                        radius=4 * s, fill=(*col, 220))
    for side in (-1, 1):
        d.ellipse((x + side * (w / 2 - 2 * s) - 2.4 * s, y - 2.6 * s,
                   x + side * (w / 2 - 2 * s) + 2.4 * s, y + 2.6 * s),
                  fill=(*acc, 240))
    d.line((x - 3 * s, y, x + 3 * s, y), fill=(*acc, 220), width=1)
    d.line((x, y - 3 * s, x, y + 3 * s), fill=(*acc, 220), width=1)
    return Image.alpha_composite(base, layer)


def vignette(base):
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    d.rectangle((0, 0, W, H), fill=255)
    for i in range(80):
        rng = random.Random(SEED + i)
        x = rng.uniform(-80, W + 80)
        y = rng.uniform(-80, H + 80)
        rr = rng.uniform(120, 260)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=240)
    layer = layer.filter(ImageFilter.GaussianBlur(40))
    dark = Image.new("RGB", (W, H), (24, 6, 20))
    return Image.composite(dark, base, layer.point(lambda v: 255 - v))


def main():
    base = Image.new("RGB", (W, H))
    for y in range(H):
        c = gradient_color(y / (H - 1))
        for x in range(W):
            base.putpixel((x, y), c)

    img = base.convert("RGBA")
    img = draw_stars(img)
    # moon + kawaii headphone face at top-center-left, girl sitting on top
    cx, cy, r = 205, 50, 27
    img = draw_moon(img, cx, cy, r)
    img = draw_girl(img, cx, cy - r + 2, s=1.0)
    img = draw_cloud(img, 60, 70, 1.0, (120, 60, 100), 80)
    img = draw_cloud(img, 340, 78, 0.8, (110, 55, 92), 65)
    img = draw_cloud(img, 420, 230, 0.9, (100, 50, 86), 55)
    img = draw_cloud(img, 52, 240, 0.7, (100, 50, 86), 50)
    img = draw_heart(img, 385, 224, 5)
    img = draw_heart(img, 402, 232, 3, color=(255, 200, 170))
    img = draw_heart(img, 96, 228, 4, color=(230, 180, 255))
    img = draw_controller(img, 390, 214, s=0.9)
    img = vignette(img.convert("RGB"))
    img = img.convert("RGB")
    img.save("img/bg_pink_preview.png")
    print("saved img/bg_pink_preview.png", img.size)


if __name__ == "__main__":
    main()
