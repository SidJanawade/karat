"""Deterministic product plates.

Real catalogues should replace these with studio shots. The renderer exists so
retrieval, evals, and the storefront work without a 10GB dataset on day one.
The visual identity is *controlled*: metal hue + gem hue + category silhouette.
That lets us prove hybrid search, not just demo a CLIP download.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from karatmatch.taxonomy import GEM_COLOR, METAL_COLOR, Category, Sku

BG = (18, 16, 14)
CARD = (32, 28, 24)


def _hex(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def render_sku(sku: Sku, dest: Path, size: int = 512) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)
    margin = 36
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=28,
        fill=CARD,
    )
    metal = _hex(METAL_COLOR[sku.attributes.metal])
    gem = _hex(GEM_COLOR[sku.attributes.gem])
    cx = cy = size // 2
    _silhouette(draw, sku.attributes.category, cx, cy, metal, gem)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        small = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small = font
    draw.text((52, size - 88), sku.sku, fill=(212, 175, 55), font=font)
    draw.text((52, size - 64), sku.attributes.category.value.replace("_", " "), fill=(180, 170, 150), font=small)
    img = img.filter(ImageFilter.SMOOTH)
    img.save(dest, format="JPEG", quality=92)
    return dest


def _silhouette(
    draw: ImageDraw.ImageDraw,
    category: Category,
    cx: int,
    cy: int,
    metal: tuple[int, int, int],
    gem: tuple[int, int, int],
) -> None:
    if category is Category.RING:
        draw.ellipse((cx - 90, cy - 90, cx + 90, cy + 90), outline=metal, width=22)
        draw.ellipse((cx - 28, cy - 118, cx + 28, cy - 62), fill=gem, outline=metal, width=6)
    elif category is Category.NECKLACE:
        draw.arc((cx - 140, cy - 80, cx + 140, cy + 200), 200, 340, fill=metal, width=10)
        draw.polygon([(cx, cy + 20), (cx - 28, cy + 90), (cx + 28, cy + 90)], fill=gem, outline=metal)
    elif category is Category.EARRING:
        draw.ellipse((cx - 24, cy - 110, cx + 24, cy - 62), fill=metal)
        draw.polygon([(cx, cy - 50), (cx - 40, cy + 70), (cx + 40, cy + 70)], fill=gem, outline=metal, width=4)
    elif category is Category.BANGLE:
        draw.ellipse((cx - 120, cy - 80, cx + 120, cy + 80), outline=metal, width=18)
        draw.ellipse((cx - 90, cy - 50, cx + 90, cy + 50), outline=gem, width=6)
    elif category is Category.BRACELET:
        draw.rounded_rectangle((cx - 140, cy - 28, cx + 140, cy + 28), radius=20, outline=metal, width=10)
        for i in range(-3, 4):
            draw.ellipse((cx + i * 32 - 10, cy - 10, cx + i * 32 + 10, cy + 10), fill=gem)
    elif category is Category.PENDANT:
        draw.line((cx, cy - 130, cx, cy - 20), fill=metal, width=6)
        draw.polygon([(cx, cy - 20), (cx - 50, cy + 80), (cx + 50, cy + 80)], fill=gem, outline=metal, width=5)
    elif category is Category.MANGALSUTRA:
        draw.arc((cx - 130, cy - 70, cx + 130, cy + 180), 200, 340, fill=metal, width=6)
        draw.ellipse((cx - 18, cy + 40, cx + 18, cy + 76), fill=(20, 20, 20), outline=metal, width=3)
        draw.ellipse((cx - 8, cy + 50, cx + 8, cy + 66), fill=gem)
    elif category is Category.MAANG_TIKKA:
        draw.line((cx, cy - 120, cx, cy - 10), fill=metal, width=4)
        draw.ellipse((cx - 36, cy - 10, cx + 36, cy + 62), fill=gem, outline=metal, width=5)
    elif category is Category.NOSE_PIN:
        draw.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=metal)
        draw.ellipse((cx + 10, cy - 8, cx + 42, cy + 24), fill=gem, outline=metal, width=3)
    elif category is Category.ANKLET:
        draw.arc((cx - 150, cy - 40, cx + 150, cy + 80), 200, 340, fill=metal, width=8)
        for i in range(-4, 5):
            draw.ellipse((cx + i * 22 - 6, cy + 36, cx + i * 22 + 6, cy + 48), fill=gem)
    else:  # SET
        draw.arc((cx - 120, cy - 100, cx + 120, cy + 140), 210, 330, fill=metal, width=8)
        draw.ellipse((cx - 70, cy + 40, cx - 30, cy + 80), fill=gem, outline=metal, width=4)
        draw.ellipse((cx + 30, cy + 40, cx + 70, cy + 80), fill=gem, outline=metal, width=4)
        draw.ellipse((cx - 18, cy - 10, cx + 18, cy + 26), fill=gem)
