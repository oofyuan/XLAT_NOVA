#!/usr/bin/env python3
"""Generate a plain solid black 480x272 background (no logo)."""

from PIL import Image

OUT_PREVIEW = "img/bg_black_preview.png"
W, H = 480, 272


def main():
    bg = Image.new("RGB", (W, H), (0, 0, 0))
    bg.save(OUT_PREVIEW)
    print("saved", OUT_PREVIEW, bg.size)


if __name__ == "__main__":
    main()
