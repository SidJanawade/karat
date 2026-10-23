from __future__ import annotations

import json
import random
from itertools import product

from karatmatch.config import settings
from karatmatch.embeddings import CatalogIndex
from karatmatch.images import render_sku
from karatmatch.taxonomy import (
    Category,
    Gem,
    Metal,
    Occasion,
    Purity,
    Region,
    Sku,
    Style,
)

TITLE = {
    Category.RING: "Ring",
    Category.NECKLACE: "Necklace",
    Category.EARRING: "Jhumkas",
    Category.BANGLE: "Bangles",
    Category.BRACELET: "Bracelet",
    Category.PENDANT: "Pendant",
    Category.MANGALSUTRA: "Mangalsutra",
    Category.MAANG_TIKKA: "Maang Tikka",
    Category.NOSE_PIN: "Nose Pin",
    Category.ANKLET: "Payal",
    Category.SET: "Bridal Set",
}

WEIGHT = {
    Category.RING: (2.4, 6.8),
    Category.NECKLACE: (12.0, 38.0),
    Category.EARRING: (4.0, 14.0),
    Category.BANGLE: (16.0, 40.0),
    Category.BRACELET: (8.0, 18.0),
    Category.PENDANT: (2.8, 8.5),
    Category.MANGALSUTRA: (6.0, 16.0),
    Category.MAANG_TIKKA: (3.0, 9.0),
    Category.NOSE_PIN: (0.6, 2.2),
    Category.ANKLET: (8.0, 18.0),
    Category.SET: (28.0, 72.0),
}


def _sku(
    rng: random.Random,
    n: int,
    category: Category,
    style: Style,
    metal: Metal,
    purity: Purity,
    gem: Gem,
    occasion: Occasion,
    region: Region,
    vendor: str,
    stock: int,
    unique: bool,
    duplicate_of: str | None = None,
) -> Sku:
    lo, hi = WEIGHT[category]
    noun = TITLE[category]
    metal_label = metal.value.replace("_", " ")
    gem_label = "" if gem is Gem.NONE else f" {gem.value}"
    title = f"{purity.value} {metal_label}{gem_label} {style.value} {noun}".title()
    desc = (
        f"{region.value.replace('_', ' ')} {occasion.value} wear. "
        f"Hand-finished {style.value} {noun.lower()} in {purity.value} {metal_label}."
    )
    sku_id = f"KM-{n:04d}"
    return Sku(
        sku=sku_id,
        title=title,
        description=desc,
        vendor_id=vendor,
        attributes={
            "category": category,
            "style": style,
            "metal": metal,
            "purity": purity,
            "gem": gem,
            "occasion": occasion,
            "region": region,
        },
        weight_grams=round(rng.uniform(lo, hi), 2),
        making_charge_pct=round(rng.uniform(8.0, 18.0), 1),
        stone_value_inr=0.0 if gem is Gem.NONE else round(rng.uniform(2500, 45000), 0),
        stock_qty=stock,
        unique_piece=unique,
        image_name=f"{sku_id}.jpg",
        duplicate_of=duplicate_of,
    )


def build_catalog(count: int = 220, seed: int = 7) -> list[Sku]:
    rng = random.Random(seed)
    combos = list(
        product(
            list(Category),
            [Style.TEMPLE, Style.KUNDAN, Style.POLKI, Style.CONTEMPORARY, Style.MINIMAL, Style.BRIDAL],
            [Metal.GOLD, Metal.ROSE_GOLD, Metal.WHITE_GOLD, Metal.SILVER],
            [Purity.K22, Purity.K18, Purity.S925],
            [Gem.NONE, Gem.DIAMOND, Gem.RUBY, Gem.EMERALD, Gem.PEARL, Gem.POLKI],
            [Occasion.DAILY, Occasion.WEDDING, Occasion.FESTIVE, Occasion.ENGAGEMENT],
            [Region.SOUTH, Region.NORTH, Region.PAN_INDIA],
        )
    )
    rng.shuffle(combos)
    skus: list[Sku] = []
    n = 1
    for combo in combos:
        category, style, metal, purity, gem, occasion, region = combo
        if metal is Metal.SILVER and purity is not Purity.S925:
            continue
        if metal is not Metal.SILVER and purity is Purity.S925:
            continue
        if style is Style.TEMPLE and region is Region.NORTH:
            continue
        vendor = rng.choice(["aurum-house", "meenakari-co", "nizam-atelier", "coastal-gold"])
        stock = 0 if rng.random() < 0.08 else rng.randint(1, 14)
        unique = category in {Category.SET, Category.NECKLACE} and rng.random() < 0.2
        skus.append(
            _sku(rng, n, category, style, metal, purity, gem, occasion, region, vendor, stock, unique)
        )
        n += 1
        if len(skus) >= count:
            break

    # Intentional near-duplicates: same visual recipe, different vendor SKU.
    # This is the inventory problem: two listings, one design.
    for src in skus[:8]:
        clone = src.model_copy(
            update={
                "sku": f"KM-{n:04d}",
                "vendor_id": "mirror-imports",
                "title": src.title.replace("Gold", "Gold "),
                "image_name": f"KM-{n:04d}.jpg",
                "duplicate_of": src.sku,
                "stock_qty": rng.randint(1, 5),
            }
        )
        skus.append(clone)
        n += 1
    return skus


def persist(skus: list[Sku]) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    for sku in skus:
        src = next((s for s in skus if s.sku == sku.duplicate_of), None)
        if src is not None:
            # Same pixels as the source SKU — classic supplier duplicate.
            render_sku(src, settings.images_dir / sku.image_name)
        else:
            render_sku(sku, settings.images_dir / sku.image_name)
    payload = [s.model_dump(mode="json") for s in skus]
    settings.catalog_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    index = CatalogIndex.build(skus, settings.images_dir)
    index.save(settings.index_path)


def load_skus() -> list[Sku]:
    raw = json.loads(settings.catalog_path.read_text(encoding="utf-8"))
    return [Sku.model_validate(row) for row in raw]


def main() -> None:
    skus = build_catalog()
    persist(skus)
    print(f"seeded {len(skus)} SKUs -> {settings.catalog_path}")


if __name__ == "__main__":
    main()
