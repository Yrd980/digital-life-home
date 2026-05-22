#!/usr/bin/env python3
"""Generate compact Miri Deck page assets.

This is a deterministic fallback asset pipeline. AI-generated replacements can
drop in with the same filenames later.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "asset" / "opt"


def glow(size: tuple[int, int], center: tuple[int, int], color: tuple[int, int, int, int], radius: int) -> Image.Image:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x, y = center
    d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    return img.filter(ImageFilter.GaussianBlur(radius // 2))


def save_webp(img: Image.Image, name: str) -> None:
    img.save(OUT / name, "WEBP", quality=88, method=6)


def logo_mark() -> None:
    size = (180, 120)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.alpha_composite(glow(size, (92, 62), (121, 255, 210, 70), 42))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((34, 28, 146, 92), radius=18, fill=(7, 13, 19, 235), outline=(80, 116, 126, 255), width=3)
    d.rounded_rectangle((52, 40, 128, 76), radius=10, fill=(9, 28, 32, 255), outline=(240, 198, 109, 230), width=2)
    d.ellipse((72, 52, 82, 62), fill=(121, 255, 210, 255))
    d.ellipse((98, 52, 108, 62), fill=(121, 255, 210, 255))
    d.arc((72, 50, 108, 78), 25, 155, fill=(240, 198, 109, 230), width=2)
    d.line((56, 92, 124, 92), fill=(240, 198, 109, 180), width=2)
    d.line((68, 98, 112, 98), fill=(121, 255, 210, 140), width=1)
    save_webp(img, "pocket-logo-mark.webp")


def robot_neutral() -> None:
    size = (320, 213)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.alpha_composite(glow(size, (162, 108), (121, 255, 210, 46), 72))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((112, 42, 208, 120), radius=22, fill=(10, 20, 28, 245), outline=(73, 106, 126, 255), width=4)
    d.rounded_rectangle((128, 61, 192, 93), radius=10, fill=(8, 31, 34, 255), outline=(240, 198, 109, 210), width=2)
    d.ellipse((142, 73, 151, 82), fill=(121, 255, 210, 255))
    d.ellipse((169, 73, 178, 82), fill=(121, 255, 210, 255))
    d.line((148, 98, 174, 98), fill=(185, 218, 190, 220), width=2)
    d.rounded_rectangle((123, 120, 197, 176), radius=16, fill=(18, 24, 31, 245), outline=(87, 77, 57, 230), width=3)
    d.ellipse((148, 137, 172, 161), outline=(240, 198, 109, 210), width=3)
    d.line((122, 140, 88, 156), fill=(73, 106, 126, 255), width=5)
    d.line((198, 140, 232, 156), fill=(73, 106, 126, 255), width=5)
    d.rounded_rectangle((128, 176, 150, 194), radius=5, fill=(24, 32, 40, 255), outline=(73, 106, 126, 255), width=2)
    d.rounded_rectangle((170, 176, 192, 194), radius=5, fill=(24, 32, 40, 255), outline=(73, 106, 126, 255), width=2)
    save_webp(img, "robot-neutral.webp")


def prop(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], idx: int) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    amber = (240, 198, 109, 255)
    mint = (121, 255, 210, 255)
    rose = (238, 135, 156, 255)
    blue = (89, 136, 190, 255)
    dark = (12, 20, 29, 238)
    if idx == 0:
        draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=dark, outline=amber, width=3)
        draw.line((cx, cy - 22, cx, cy + 22), fill=mint, width=2)
    elif idx == 1:
        draw.polygon([(cx, cy - 24), (cx + 20, cy), (cx, cy + 24), (cx - 20, cy)], fill=dark, outline=mint)
        draw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=amber)
    elif idx == 2:
        draw.rounded_rectangle((cx - 20, cy - 18, cx + 20, cy + 18), radius=8, fill=dark, outline=amber, width=3)
        draw.line((cx - 12, cy, cx - 2, cy + 10, cx + 14, cy - 11), fill=mint, width=3)
    elif idx == 3:
        draw.rounded_rectangle((cx - 22, cy - 15, cx + 22, cy + 15), radius=4, fill=dark, outline=rose, width=3)
        draw.line((cx - 21, cy - 13, cx, cy + 4, cx + 21, cy - 13), fill=amber, width=2)
    elif idx == 4:
        draw.rounded_rectangle((cx - 12, cy - 23, cx + 12, cy + 23), radius=8, fill=dark, outline=mint, width=3)
        draw.arc((cx - 16, cy - 27, cx + 16, cy + 3), 200, 340, fill=amber, width=3)
    elif idx == 5:
        draw.rounded_rectangle((cx - 19, cy - 22, cx + 19, cy + 22), radius=5, fill=dark, outline=blue, width=3)
        draw.line((cx - 10, cy - 8, cx + 10, cy - 8), fill=amber, width=2)
        draw.line((cx - 10, cy + 4, cx + 10, cy + 4), fill=mint, width=2)
    elif idx == 6:
        draw.rounded_rectangle((cx - 22, cy - 17, cx + 22, cy + 17), radius=6, fill=dark, outline=mint, width=3)
        draw.polygon([(cx, cy - 11), (cx + 10, cy), (cx, cy + 11), (cx - 10, cy)], outline=amber, fill=None)
    elif idx == 7:
        draw.arc((cx - 24, cy - 24, cx + 24, cy + 24), 35, 325, fill=mint, width=4)
        draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=amber)
    elif idx == 8:
        draw.ellipse((cx - 22, cy - 18, cx + 22, cy + 18), outline=blue, width=3)
        draw.line((cx, cy + 18, cx, cy + 28), fill=blue, width=3)
        draw.line((cx - 11, cy - 6, cx + 11, cy + 6), fill=mint, width=2)
    elif idx == 9:
        draw.rounded_rectangle((cx - 24, cy - 16, cx + 24, cy + 16), radius=7, fill=dark, outline=amber, width=3)
        draw.ellipse((cx - 12, cy - 8, cx - 2, cy + 2), fill=mint)
        draw.ellipse((cx + 4, cy - 2, cx + 14, cy + 8), fill=rose)
    elif idx == 10:
        draw.rounded_rectangle((cx - 20, cy - 21, cx + 20, cy + 21), radius=12, fill=dark, outline=rose, width=3)
        draw.line((cx - 10, cy - 4, cx + 10, cy - 4), fill=amber, width=2)
        draw.line((cx - 8, cy + 8, cx + 8, cy + 8), fill=mint, width=2)
    else:
        draw.rounded_rectangle((cx - 20, cy - 20, cx + 20, cy + 20), radius=8, fill=dark, outline=blue, width=3)
        draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), outline=amber, width=3)
        draw.line((cx, cy - 18, cx, cy - 12), fill=mint, width=2)


def ritual_props() -> None:
    img = Image.new("RGBA", (384, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for idx in range(12):
        col, row = idx % 6, idx // 6
        prop(d, (col * 64, row * 64, col * 64 + 64, row * 64 + 64), idx)
    img.save(OUT / "ritual-props-sprite.png")


def theme_thumbs() -> None:
    img = Image.new("RGB", (640, 160), (6, 8, 11))
    palettes = [
        ((9, 18, 27), (121, 255, 210), (240, 198, 109)),
        ((24, 17, 12), (255, 180, 95), (121, 255, 210)),
        ((9, 11, 24), (92, 112, 190), (238, 135, 156)),
        ((9, 10, 10), (190, 198, 190), (100, 120, 110)),
    ]
    d = ImageDraw.Draw(img)
    for i, (bg, glowc, lamp) in enumerate(palettes):
        x = i * 160
        d.rectangle((x, 0, x + 160, 160), fill=bg)
        cell = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        cell.alpha_composite(glow((160, 160), (104, 58), (*glowc, 70), 48))
        img.paste(Image.alpha_composite(Image.new("RGBA", (160, 160), (*bg, 255)), cell).convert("RGB"), (x, 0))
        d.rounded_rectangle((x + 28, 38, x + 132, 120), radius=12, outline=lamp, width=3)
        d.rectangle((x + 42, 58, x + 118, 94), fill=(bg[0] + 6, bg[1] + 12, bg[2] + 16), outline=glowc, width=2)
        d.line((x + 35, 122, x + 125, 122), fill=lamp, width=2)
    save_webp(img, "theme-thumbs.webp")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logo_mark()
    robot_neutral()
    ritual_props()
    theme_thumbs()
    print("generated page assets in", OUT)


if __name__ == "__main__":
    main()
