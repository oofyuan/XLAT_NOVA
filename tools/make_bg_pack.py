#!/usr/bin/env python3
"""Generate a pack of 10 cyberpunk / anime backgrounds for the XLAT LCD.

All designs are kept dark so the white UI text stays readable. Each design
gets a readability overlay that darkens the top-right text zone and the
bottom button strip.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 480, 272
OUT = "img/bg_previews"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_base(stops):
    img = Image.new("RGB", (W, H))
    for y in range(H):
        t = y / (H - 1)
        c = stops[0][1]
        for i in range(len(stops) - 1):
            if t <= stops[i + 1][0]:
                f = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
                c = lerp(stops[i][1], stops[i + 1][1], f)
                break
        for x in range(W):
            img.putpixel((x, y), c)
    return img.convert("RGBA")


def overlay(base, layer):
    return Image.alpha_composite(base, layer)


def new_layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def stars_layer(rng, n, ymax=0.85, palette=None, twinkle=0):
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    palette = palette or [(255, 255, 255), (255, 235, 200), (200, 220, 255)]
    for _ in range(n):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H * ymax)
        r = rng.choice([1, 1, 1, 2])
        col = rng.choice(palette)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*col, rng.randint(60, 200)))
    for _ in range(twinkle):
        x = rng.uniform(20, W - 20)
        y = rng.uniform(8, H * 0.6)
        r = rng.uniform(2.5, 4.5)
        col = rng.choice(palette)
        d.line((x - r * 2.4, y, x + r * 2.4, y), fill=(*col, 220), width=1)
        d.line((x, y - r * 2.4, x, y + r * 2.4), fill=(*col, 220), width=1)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*col, 230))
    return layer


def vignette(img, strength=0.82):
    layer = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(layer)
    d.rectangle((0, 0, W, H), fill=255)
    rng = random.Random(7)
    for _ in range(70):
        x = rng.uniform(-60, W + 60)
        y = rng.uniform(-60, H + 60)
        rr = rng.uniform(140, 280)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=235)
    layer = layer.filter(ImageFilter.GaussianBlur(35))
    dark = Image.new("RGB", (W, H), (5, 4, 12))
    out = Image.composite(dark, img.convert("RGB"), layer.point(lambda v: int((255 - v) * strength)))
    return out.convert("RGBA")


def readability(img):
    """Darken the top-right text zone and the bottom strip."""
    out = img.convert("RGBA")
    # top-right quadrant
    tr = new_layer()
    d = ImageDraw.Draw(tr)
    d.polygon([(240, 0), (W, 0), (W, 130), (240, 130)], fill=(8, 6, 18, 110))
    tr = tr.filter(ImageFilter.GaussianBlur(14))
    out = overlay(out, tr)
    # bottom strip
    bt = new_layer()
    d = ImageDraw.Draw(bt)
    d.rectangle((0, H - 62, W, H), fill=(8, 6, 18, 90))
    bt = bt.filter(ImageFilter.GaussianBlur(10))
    out = overlay(out, bt)
    return out


def save(img, name):
    img = readability(vignette(img))
    img.convert("RGB").save(os.path.join(OUT, name))
    print("saved", name)


# --------------------------------------------------------------------------
# 01 cyberpunk city
# --------------------------------------------------------------------------
def design_01():
    rng = random.Random(1)
    img = make_base([(0, (10, 14, 40)), (0.55, (24, 20, 60)), (0.85, (70, 30, 90)), (1.0, (30, 24, 60))])
    img = overlay(img, stars_layer(rng, 90, twinkle=6))
    # neon moon (cyan ring)
    moon = new_layer()
    d = ImageDraw.Draw(moon)
    d.ellipse((330, 36, 390, 96), outline=(120, 240, 255, 200), width=3)
    d.ellipse((336, 42, 384, 90), outline=(80, 200, 255, 90), width=8)
    moon = moon.filter(ImageFilter.GaussianBlur(1))
    img = overlay(img, moon)
    # skyline silhouette
    sky = new_layer()
    d = ImageDraw.Draw(sky)
    ground_y = 205
    x = 0
    while x < W:
        bw = rng.randint(26, 56)
        bh = rng.randint(30, 120)
        d.rectangle((x, ground_y - bh, x + bw, ground_y), fill=(8, 8, 24, 255))
        # neon windows
        for wy in range(ground_y - bh + 6, ground_y - 4, 7):
            for wx in range(x + 4, x + bw - 3, 7):
                if rng.random() < 0.35:
                    col = rng.choice([(255, 120, 220, 230), (120, 240, 255, 230), (255, 220, 120, 230)])
                    d.rectangle((wx, wy, wx + 3, wy + 3), fill=col)
        x += bw + 4
    img = overlay(img, sky)
    # neon ground grid
    grid = new_layer()
    d = ImageDraw.Draw(grid)
    vx, vy = W // 2, ground_y
    for i in range(-14, 15):
        x0 = vx + i * 18
        d.line((x0, ground_y, vx + i * 60, H), fill=(255, 80, 200, 160), width=1)
    for yy in range(ground_y + 8, H, 8):
        d.line((0, yy, W, yy), fill=(255, 80, 200, 120), width=1)
    grid = grid.filter(ImageFilter.GaussianBlur(0.8))
    img = overlay(img, grid)
    return img


# --------------------------------------------------------------------------
# 02 anime girl on crescent moon
# --------------------------------------------------------------------------
def girl_silhouette(gx, gy, s, col, hair):
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    for side in (-1, 1):
        d.ellipse((gx + side * 4 * s - 3.4 * s, gy - 14 * s, gx + side * 4 * s + 3.4 * s, gy + 2 * s), fill=hair)
        d.ellipse((gx + side * 4 * s - 1.6 * s, gy - 11 * s, gx + side * 4 * s + 1.6 * s, gy - 5 * s),
                  fill=tuple(min(255, c + 60) for c in hair))
    d.polygon([(gx - 5 * s, gy - 6 * s), (gx + 5 * s, gy - 6 * s),
               (gx + 7 * s, gy + 7 * s), (gx - 7 * s, gy + 7 * s)], fill=col)
    d.rounded_rectangle((gx - 4 * s, gy - 10 * s, gx + 4 * s, gy - 4 * s), radius=2 * s, fill=col)
    d.ellipse((gx - 5.5 * s, gy - 19 * s, gx + 5.5 * s, gy - 7 * s), fill=col)
    d.ellipse((gx - 4 * s, gy - 18 * s, gx - 1 * s, gy - 13 * s), fill=tuple(min(255, c + 70) for c in hair))
    return layer


def design_02():
    rng = random.Random(2)
    img = make_base([(0, (16, 18, 60)), (0.5, (40, 30, 90)), (0.8, (110, 60, 120)), (1.0, (70, 50, 110))])
    img = overlay(img, stars_layer(rng, 140, twinkle=10,
                                   palette=[(255, 255, 255), (255, 220, 235), (220, 200, 255)]))
    # crescent moon
    cx, cy, r = 210, 60, 44
    glow = new_layer()
    d = ImageDraw.Draw(glow)
    d.ellipse((cx - r * 1.9, cy - r * 1.9, cx + r * 1.9, cy + r * 1.9), fill=(255, 235, 220, 60))
    img = overlay(img, glow.filter(ImageFilter.GaussianBlur(16)))
    moon = new_layer()
    d = ImageDraw.Draw(moon)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 244, 230, 255))
    cut = Image.new("L", (W, H), 0)
    d2 = ImageDraw.Draw(cut)
    d2.ellipse((cx - r + 18, cy - r - 8, cx + r + 20, cy + r + 8), fill=255)
    moon = Image.composite(new_layer(), moon, cut.point(lambda v: 255 - v))
    img = overlay(img, moon)
    # girl sitting in the crescent
    img = overlay(img, girl_silhouette(cx + 6, cy + 6, 1.15, (56, 20, 60), (255, 170, 200)))
    # sparkles
    sp = new_layer()
    d = ImageDraw.Draw(sp)
    for x, y in [(120, 90), (330, 60), (370, 130), (80, 150)]:
        d.line((x - 6, y, x + 6, y), fill=(255, 255, 255, 200), width=1)
        d.line((x, y - 6, x, y + 6), fill=(255, 255, 255, 200), width=1)
    img = overlay(img, sp)
    return img


# --------------------------------------------------------------------------
# 03 synthwave grid + striped sun
# --------------------------------------------------------------------------
def design_03():
    rng = random.Random(3)
    img = make_base([(0, (10, 8, 30)), (0.72, (40, 12, 60)), (1.0, (60, 16, 80))])
    img = overlay(img, stars_layer(rng, 120, twinkle=8))
    # striped sun on horizon
    cx, cy, r = 240, 130, 62
    sun = new_layer()
    d = ImageDraw.Draw(sun)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 120, 200, 255))
    mask = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(mask)
    dm.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    for yy in range(cy - r, cy + r, 7):
        dm.rectangle((0, yy, W, yy + 3), fill=0)
    sun = Image.composite(new_layer(), sun, mask)
    sun = sun.filter(ImageFilter.GaussianBlur(1))
    img = overlay(img, sun)
    # perspective grid
    grid = new_layer()
    d = ImageDraw.Draw(grid)
    horizon = 148
    vx, vy = W // 2, horizon
    for i in range(-20, 21):
        d.line((vx + i * 16, horizon, vx + i * 90, H), fill=(0, 255, 220, 170), width=1)
    for yy in range(horizon + 10, H, 10):
        d.line((0, yy, W, yy), fill=(0, 255, 220, 150), width=1)
    grid = grid.filter(ImageFilter.GaussianBlur(0.6))
    img = overlay(img, grid)
    return img


# --------------------------------------------------------------------------
# 04 cyber cat
# --------------------------------------------------------------------------
def design_04():
    rng = random.Random(4)
    img = make_base([(0, (8, 12, 34)), (0.6, (20, 22, 60)), (1.0, (40, 20, 70))])
    img = overlay(img, stars_layer(rng, 80, twinkle=5,
                                   palette=[(255, 255, 255), (160, 230, 255), (255, 170, 220)]))
    # faint circuit pattern
    cir = new_layer()
    d = ImageDraw.Draw(cir)
    for i in range(26):
        x = rng.randint(0, W)
        y = rng.randint(0, H)
        w = rng.randint(10, 40)
        col = rng.choice([(80, 220, 255, 40), (255, 90, 200, 40)])
        d.line((x, y, x + w, y), fill=col)
        d.line((x + w, y, x + w, y + rng.randint(6, 18)), fill=col)
        d.ellipse((x + w - 2, y - 2, x + w + 2, y + 2), fill=col)
    img = overlay(img, cir)
    # cat
    cat = new_layer()
    d = ImageDraw.Draw(cat)
    gx, gy = 240, 170
    d.ellipse((gx - 46, gy - 34, gx + 46, gy + 40), fill=(10, 10, 26, 255))
    d.polygon([(gx - 46, gy - 20), (gx - 60, gy - 62), (gx - 30, gy - 40)], fill=(10, 10, 26, 255))
    d.polygon([(gx + 46, gy - 20), (gx + 60, gy - 62), (gx + 30, gy - 40)], fill=(10, 10, 26, 255))
    # glowing eyes
    for ex in (gx - 20, gx + 20):
        d.ellipse((ex - 7, gy - 8, ex + 7, gy + 4), fill=(120, 240, 255, 255))
    d.ellipse((gx - 20 - 2, gy - 4, gx - 20 + 2, gy + 2), fill=(10, 10, 26, 255))
    d.ellipse((gx + 20 - 2, gy - 4, gx + 20 + 2, gy + 2), fill=(10, 10, 26, 255))
    # neon ear tips
    d.polygon([(gx - 58, gy - 58), (gx - 50, gy - 70), (gx - 44, gy - 54)], fill=(255, 90, 200, 255))
    d.polygon([(gx + 44, gy - 54), (gx + 50, gy - 70), (gx + 58, gy - 58)], fill=(255, 90, 200, 255))
    cat = cat.filter(ImageFilter.GaussianBlur(0.4))
    img = overlay(img, cat)
    # neon collar
    col2 = new_layer()
    d = ImageDraw.Draw(col2)
    d.arc((gx - 30, gy + 18, gx + 30, gy + 46), start=0, end=180, fill=(255, 90, 200, 220), width=3)
    d.ellipse((gx - 3, gy + 28, gx + 3, gy + 34), fill=(120, 240, 255, 255))
    img = overlay(img, col2)
    return img


# --------------------------------------------------------------------------
# 05 anime sunset
# --------------------------------------------------------------------------
def design_05():
    rng = random.Random(5)
    img = make_base([(0, (24, 20, 60)), (0.45, (70, 40, 100)), (0.72, (200, 90, 120)), (1.0, (240, 140, 110))])
    # anime clouds (elongated horizontal blobs)
    cloud = new_layer()
    d = ImageDraw.Draw(cloud)
    for cy, alpha, col in [(60, 120, (255, 200, 210)), (95, 100, (255, 170, 190)), (130, 80, (255, 220, 200))]:
        x = 40
        while x < W - 60:
            w = rng.randint(40, 110)
            d.rounded_rectangle((x, cy, x + w, cy + 7), radius=4, fill=(*col, alpha))
            x += w + rng.randint(20, 80)
    cloud = cloud.filter(ImageFilter.GaussianBlur(2))
    img = overlay(img, cloud)
    # sun
    sun = new_layer()
    d = ImageDraw.Draw(sun)
    d.ellipse((180, 150, 300, 210), fill=(255, 235, 190, 255))
    img = overlay(img, sun.filter(ImageFilter.GaussianBlur(2)))
    # hill silhouette + small girl
    hill = new_layer()
    d = ImageDraw.Draw(hill)
    d.polygon([(0, H), (0, 210), (150, 178), (320, 196), (W, 176), (W, H)], fill=(30, 20, 48, 255))
    img = overlay(img, hill)
    img = overlay(img, girl_silhouette(180, 168, 0.9, (30, 20, 48), (255, 160, 190)))
    # birds
    bird = new_layer()
    d = ImageDraw.Draw(bird)
    for bx, by in [(90, 110), (120, 96), (400, 80)]:
        d.arc((bx - 8, by - 4, bx, by + 4), 0, 180, fill=(40, 30, 60, 220), width=2)
        d.arc((bx, by - 4, bx + 8, by + 4), 0, 180, fill=(40, 30, 60, 220), width=2)
    img = overlay(img, bird)
    return img


# --------------------------------------------------------------------------
# 06 galaxy
# --------------------------------------------------------------------------
def design_06():
    rng = random.Random(6)
    img = make_base([(0, (6, 8, 30)), (0.6, (24, 18, 60)), (1.0, (50, 24, 80))])
    # nebula blobs along a spiral-ish path
    neb = new_layer()
    d = ImageDraw.Draw(neb)
    for i in range(22):
        t = i / 22
        x = W * 0.5 + math.sin(t * 9 + 1.2) * (70 + t * 90)
        y = H * (0.25 + t * 0.55)
        r = rng.uniform(22, 60) * (1 - t * 0.4)
        col = rng.choice([(80, 60, 180, 70), (150, 60, 160, 60), (60, 120, 200, 60), (200, 90, 160, 55)])
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    neb = neb.filter(ImageFilter.GaussianBlur(28))
    img = overlay(img, neb)
    img = overlay(img, stars_layer(rng, 220, ymax=1.0, twinkle=12,
                                   palette=[(255, 255, 255), (190, 220, 255), (255, 200, 230)]))
    # shooting star
    shoot = new_layer()
    d = ImageDraw.Draw(shoot)
    d.line((60, 60, 150, 108), fill=(255, 255, 255, 220), width=2)
    d.line((150, 108, 190, 126), fill=(255, 255, 255, 90), width=1)
    img = overlay(img, shoot)
    return img


# --------------------------------------------------------------------------
# 07 neon torii
# --------------------------------------------------------------------------
def design_07():
    rng = random.Random(7)
    img = make_base([(0, (12, 14, 44)), (0.6, (30, 24, 70)), (1.0, (60, 30, 90))])
    img = overlay(img, stars_layer(rng, 130, twinkle=10))
    # moon behind torii
    moon = new_layer()
    d = ImageDraw.Draw(moon)
    d.ellipse((190, 40, 290, 140), fill=(255, 240, 220, 255))
    img = overlay(img, moon.filter(ImageFilter.GaussianBlur(1)))
    # torii gate (neon red)
    torii = new_layer()
    d = ImageDraw.Draw(torii)
    red = (255, 80, 90)
    d.arc((40, 60, 440, 150), 0, 180, fill=(*red, 255), width=9)
    d.line((70, 120, 70, H), fill=(*red, 255), width=8)
    d.line((410, 120, 410, H), fill=(*red, 255), width=8)
    d.line((60, 116, 420, 116), fill=(*red, 255), width=7)
    d.arc((40, 60, 440, 150), 0, 180, fill=(255, 160, 120, 90), width=18)
    torii = torii.filter(ImageFilter.GaussianBlur(1))
    img = overlay(img, torii)
    # sakura petals
    pet = new_layer()
    d = ImageDraw.Draw(pet)
    for _ in range(24):
        x = rng.randint(0, W)
        y = rng.randint(60, H)
        d.ellipse((x, y, x + 4, y + 3), fill=(255, 170, 200, rng.randint(120, 210)))
    img = overlay(img, pet)
    return img


# --------------------------------------------------------------------------
# 08 matrix rain
# --------------------------------------------------------------------------
def design_08():
    rng = random.Random(8)
    img = make_base([(0, (2, 10, 8)), (0.7, (4, 24, 16)), (1.0, (8, 36, 22))])
    rain = new_layer()
    d = ImageDraw.Draw(rain)
    try:
        font = ImageFont.load_default(size=9)
    except TypeError:
        font = ImageFont.load_default()
    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ"
    cols = list(range(6, W - 4, 13))
    for x in cols:
        length = rng.randint(12, 42)
        y0 = rng.randint(-H, 0)
        for i in range(length):
            y = y0 + i * 13
            if 0 <= y < H:
                ch = chars[rng.randrange(len(chars))]
                head = (i == length - 1)
                col = (200, 255, 220, 230) if head else (0, 230, 120, rng.randint(60, 170))
                d.text((x, y), ch, font=font, fill=col)
    rain = rain.filter(ImageFilter.GaussianBlur(0.3))
    img = overlay(img, rain)
    # slight neon green tint
    tint = new_layer()
    d = ImageDraw.Draw(tint)
    d.rectangle((0, 0, W, H), fill=(0, 40, 20, 30))
    img = overlay(img, tint)
    return img


# --------------------------------------------------------------------------
# 09 cyberpunk girl (neon hair)
# --------------------------------------------------------------------------
def design_09():
    rng = random.Random(9)
    img = make_base([(0, (10, 12, 38)), (0.55, (30, 20, 66)), (1.0, (60, 26, 80))])
    img = overlay(img, stars_layer(rng, 90, twinkle=6,
                                   palette=[(255, 255, 255), (140, 240, 255), (255, 130, 220)]))
    # big neon circle behind girl (glitch halo)
    halo = new_layer()
    d = ImageDraw.Draw(halo)
    d.ellipse((150, 70, 330, 250), outline=(255, 90, 200, 90), width=2)
    d.ellipse((170, 90, 310, 230), outline=(120, 240, 255, 60), width=1)
    img = overlay(img, halo)
    # girl with neon hair
    girl = new_layer()
    d = ImageDraw.Draw(girl)
    gx, gy = 240, 150
    hair_pink = (255, 90, 200)
    hair_cyan = (120, 240, 255)
    # hair mass (neon)
    for side in (-1, 1):
        d.ellipse((gx + side * 26 - 20, gy - 60, gx + side * 26 + 20, gy + 30), fill=(*hair_pink, 255))
        d.ellipse((gx + side * 34 - 14, gy - 40, gx + side * 34 + 14, gy + 44), fill=(*hair_cyan, 255))
    # face/body silhouette
    d.ellipse((gx - 22, gy - 52, gx + 22, gy - 8), fill=(12, 10, 30, 255))
    d.rounded_rectangle((gx - 26, gy - 10, gx + 26, gy + 46), radius=12, fill=(12, 10, 30, 255))
    # visor (neon)
    d.rounded_rectangle((gx - 24, gy - 26, gx + 24, gy - 16), radius=4, fill=(120, 240, 255, 255))
    d.rounded_rectangle((gx - 24, gy - 26, gx - 6, gy - 16), radius=4, fill=(200, 255, 255, 255))
    # headphones
    d.arc((gx - 30, gy - 60, gx + 30, gy), start=180, end=360, fill=(12, 10, 30, 255), width=5)
    d.rounded_rectangle((gx - 32, gy - 34, gx - 24, gy - 4), radius=3, fill=(12, 10, 30, 255))
    d.rounded_rectangle((gx + 24, gy - 34, gx + 32, gy - 4), radius=3, fill=(12, 10, 30, 255))
    girl = girl.filter(ImageFilter.GaussianBlur(0.5))
    img = overlay(img, girl)
    # neon accents
    acc = new_layer()
    d = ImageDraw.Draw(acc)
    d.line((60, 210, 130, 210), fill=(255, 90, 200, 200), width=2)
    d.line((350, 190, 420, 190), fill=(120, 240, 255, 200), width=2)
    d.ellipse((404, 178, 412, 186), fill=(255, 255, 255, 220))
    img = overlay(img, acc)
    return img


# --------------------------------------------------------------------------
# 10 vaporwave
# --------------------------------------------------------------------------
def design_10():
    rng = random.Random(10)
    img = make_base([(0, (20, 14, 60)), (0.5, (90, 40, 120)), (0.78, (240, 110, 160)), (1.0, (250, 160, 130))])
    # retro sun
    cx, cy, r = 240, 120, 64
    sun = new_layer()
    d = ImageDraw.Draw(sun)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 190, 140, 255))
    mask = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(mask)
    dm.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    for yy in range(cy - r, cy + r, 8):
        dm.rectangle((0, yy, W, yy + 3), fill=0)
    sun = Image.composite(new_layer(), sun, mask).filter(ImageFilter.GaussianBlur(1))
    img = overlay(img, sun)
    # palm tree
    palm = new_layer()
    d = ImageDraw.Draw(palm)
    d.line((100, H, 100, 120), fill=(16, 12, 40, 255), width=6)
    d.line((100, 200, 130, 170), fill=(16, 12, 40, 255), width=4)
    d.line((100, 250, 68, 222), fill=(16, 12, 40, 255), width=4)
    for bx, by, ang in [(130, 166, 0), (150, 150, 20), (118, 152, -20), (142, 172, 40)]:
        d.arc((bx - 22, by - 10, bx + 22, by + 14), start=ang, end=ang + 180,
              fill=(16, 12, 40, 255), width=4)
    img = overlay(img, palm)
    # grid
    grid = new_layer()
    d = ImageDraw.Draw(grid)
    horizon = 160
    vx = W // 2
    for i in range(-18, 19):
        d.line((vx + i * 18, horizon, vx + i * 110, H), fill=(255, 120, 200, 160), width=1)
    for yy in range(horizon + 10, H, 10):
        d.line((0, yy, W, yy), fill=(255, 120, 200, 130), width=1)
    grid = grid.filter(ImageFilter.GaussianBlur(0.6))
    img = overlay(img, grid)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    designs = [
        ("opt01_cyberpunk_city.png", design_01),
        ("opt02_anime_girl_moon.png", design_02),
        ("opt03_synthwave.png", design_03),
        ("opt04_cyber_cat.png", design_04),
        ("opt05_anime_sunset.png", design_05),
        ("opt06_galaxy.png", design_06),
        ("opt07_neon_torii.png", design_07),
        ("opt08_matrix.png", design_08),
        ("opt09_cyberpunk_girl.png", design_09),
        ("opt10_vaporwave.png", design_10),
    ]
    for name, fn in designs:
        save(fn(), name)


if __name__ == "__main__":
    main()
