"""Canonical jewellery taxonomy.

Interview note: jewellery search fails when you treat it like fashion. Buyers
filter on metal, purity, stone family, setting language, and occasion — then
rank visually. Taxonomy is the contract between enrichment, NLU, and retrieval.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    RING = "ring"
    NECKLACE = "necklace"
    EARRING = "earring"
    BANGLE = "bangle"
    BRACELET = "bracelet"
    PENDANT = "pendant"
    MANGALSUTRA = "mangalsutra"
    MAANG_TIKKA = "maang_tikka"
    NOSE_PIN = "nose_pin"
    ANKLET = "anklet"
    SET = "set"


class Style(StrEnum):
    TEMPLE = "temple"
    KUNDAN = "kundan"
    POLKI = "polki"
    ANTIQUE = "antique"
    CONTEMPORARY = "contemporary"
    MINIMAL = "minimal"
    TRADITIONAL = "traditional"
    BRIDAL = "bridal"


class Metal(StrEnum):
    GOLD = "gold"
    ROSE_GOLD = "rose_gold"
    WHITE_GOLD = "white_gold"
    SILVER = "silver"
    PLATINUM = "platinum"


class Purity(StrEnum):
    K22 = "22k"
    K18 = "18k"
    K14 = "14k"
    S925 = "925"


class Gem(StrEnum):
    NONE = "none"
    DIAMOND = "diamond"
    POLKI = "polki"
    KUNDAN = "kundan"
    RUBY = "ruby"
    EMERALD = "emerald"
    SAPPHIRE = "sapphire"
    PEARL = "pearl"
    CZ = "cz"


class Occasion(StrEnum):
    DAILY = "daily"
    OFFICE = "office"
    WEDDING = "wedding"
    FESTIVE = "festive"
    ENGAGEMENT = "engagement"


class Region(StrEnum):
    SOUTH = "south"
    NORTH = "north"
    PAN_INDIA = "pan_india"


METAL_COLOR = {
    Metal.GOLD: "#D4AF37",
    Metal.ROSE_GOLD: "#B76E79",
    Metal.WHITE_GOLD: "#E8E8E8",
    Metal.SILVER: "#C0C0C0",
    Metal.PLATINUM: "#DEDEE0",
}

GEM_COLOR = {
    Gem.NONE: "#F4E7C3",
    Gem.DIAMOND: "#F5F7FA",
    Gem.POLKI: "#F3E6B3",
    Gem.KUNDAN: "#E8C547",
    Gem.RUBY: "#9B1B30",
    Gem.EMERALD: "#1F7A4D",
    Gem.SAPPHIRE: "#1E3A8A",
    Gem.PEARL: "#F8F1E7",
    Gem.CZ: "#EEF2F7",
}

PURITY_FINE = {
    Purity.K22: 22 / 24,
    Purity.K18: 18 / 24,
    Purity.K14: 14 / 24,
    Purity.S925: 0.0,  # not gold — priced as silver/platinum below
}

# (phrase, field, value) — first matching field wins for a phrase; longest phrase first.
ALIAS_RULES: list[tuple[str, str, str]] = []


def _alias(field: str, value: str, *words: str) -> None:
    for word in words:
        ALIAS_RULES.append((word.lower(), field, value))


_alias("category", Category.RING, "ring", "rings", "band")
_alias("category", Category.NECKLACE, "necklace", "haar", "haram", "chain")
_alias("category", Category.EARRING, "earring", "earrings", "jhumka", "jhumkas", "studs", "drops")
_alias("category", Category.BANGLE, "bangle", "bangles", "kada")
_alias("category", Category.BRACELET, "bracelet", "bracelets")
_alias("category", Category.PENDANT, "pendant", "locket")
_alias("category", Category.MANGALSUTRA, "mangalsutra", "thaali")
_alias("category", Category.MAANG_TIKKA, "maang tikka", "tikka", "matha patti")
_alias("category", Category.NOSE_PIN, "nose pin", "nath", "nosepin")
_alias("category", Category.ANKLET, "anklet", "payal")
_alias("category", Category.SET, "set", "bridal set")
_alias("style", Style.TEMPLE, "temple", "temple jewellery")
_alias("style", Style.KUNDAN, "kundan")
_alias("style", Style.POLKI, "polki", "uncut")
_alias("style", Style.ANTIQUE, "antique")
_alias("style", Style.CONTEMPORARY, "contemporary", "modern")
_alias("style", Style.MINIMAL, "minimal", "daily wear", "solitaire")
_alias("style", Style.TRADITIONAL, "traditional")
_alias("style", Style.BRIDAL, "bridal", "wedding jewellery")
_alias("metal", Metal.GOLD, "gold", "yellow gold")
_alias("metal", Metal.ROSE_GOLD, "rose gold", "rosegold")
_alias("metal", Metal.WHITE_GOLD, "white gold")
_alias("metal", Metal.SILVER, "silver")
_alias("metal", Metal.PLATINUM, "platinum")
_alias("purity", Purity.K22, "22k", "22kt", "22 carat")
_alias("purity", Purity.K18, "18k", "18kt")
_alias("purity", Purity.K14, "14k", "14kt")
_alias("purity", Purity.S925, "925", "sterling")
_alias("gem", Gem.DIAMOND, "diamond", "diamonds")
_alias("gem", Gem.POLKI, "polki")
_alias("gem", Gem.KUNDAN, "kundan")
_alias("gem", Gem.RUBY, "ruby", "rubies")
_alias("gem", Gem.EMERALD, "emerald")
_alias("gem", Gem.SAPPHIRE, "sapphire")
_alias("gem", Gem.PEARL, "pearl", "pearls", "moti")
_alias("gem", Gem.CZ, "cz", "american diamond")
_alias("occasion", Occasion.WEDDING, "wedding", "bridal")
_alias("occasion", Occasion.FESTIVE, "festive", "diwali", "navratri")
_alias("occasion", Occasion.OFFICE, "office", "work")
_alias("occasion", Occasion.DAILY, "daily", "everyday")
_alias("occasion", Occasion.ENGAGEMENT, "engagement")
_alias("region", Region.SOUTH, "south indian", "kanjeevaram", "tamil")
_alias("region", Region.NORTH, "north indian", "rajasthan", "jaipur")


class Attributes(BaseModel):
    category: Category
    style: Style
    metal: Metal
    purity: Purity
    gem: Gem = Gem.NONE
    occasion: Occasion = Occasion.DAILY
    region: Region = Region.PAN_INDIA


class Filters(BaseModel):
    category: Category | None = None
    style: Style | None = None
    metal: Metal | None = None
    purity: Purity | None = None
    gem: Gem | None = None
    occasion: Occasion | None = None
    region: Region | None = None
    max_price_inr: float | None = None
    in_stock_only: bool = False


class Sku(BaseModel):
    sku: str
    title: str
    description: str
    vendor_id: str
    attributes: Attributes
    weight_grams: float = Field(gt=0)
    making_charge_pct: float = Field(ge=0)
    stone_value_inr: float = Field(ge=0)
    stock_qty: int = Field(ge=0)
    unique_piece: bool = False
    image_name: str
    duplicate_of: str | None = None

    def matches(self, filters: Filters) -> bool:
        """Hard constraints only. Style/gem/occasion are ranking signals, not gates."""
        a = self.attributes
        checks = (
            (filters.category is None or a.category == filters.category),
            (filters.metal is None or a.metal == filters.metal),
            (filters.purity is None or a.purity == filters.purity),
            (not filters.in_stock_only or self.stock_qty > 0),
        )
        return all(checks)

    def soft_boost(self, filters: Filters) -> float:
        a = self.attributes
        score = 0.0
        if filters.style is not None and a.style == filters.style:
            score += 0.2
        if filters.gem is not None and a.gem == filters.gem:
            score += 0.2
        if filters.occasion is not None and a.occasion == filters.occasion:
            score += 0.12
        if filters.region is not None and a.region == filters.region:
            score += 0.08
        return score


def price_inr(sku: Sku, gold_rate_24k: float, silver_rate: float = 110.0, platinum_rate: float = 3200.0) -> float:
    """India-style quote: metal value + making % + stone value. No GST (call that out)."""
    metal = sku.attributes.metal
    if metal in {Metal.GOLD, Metal.ROSE_GOLD, Metal.WHITE_GOLD}:
        metal_value = sku.weight_grams * gold_rate_24k * PURITY_FINE[sku.attributes.purity]
    elif metal is Metal.SILVER:
        metal_value = sku.weight_grams * silver_rate
    else:
        metal_value = sku.weight_grams * platinum_rate
    making = metal_value * (sku.making_charge_pct / 100.0)
    return round(metal_value + making + sku.stone_value_inr, 2)


def missing_attributes(sku: Sku) -> list[str]:
    """Fields a marketplace listing would reject or bury in search."""
    gaps: list[str] = []
    if not sku.title.strip():
        gaps.append("title")
    if sku.weight_grams <= 0:
        gaps.append("weight_grams")
    if sku.attributes.gem is Gem.NONE and "stone" in sku.title.lower():
        gaps.append("gem")
    if sku.stock_qty == 0 and not sku.unique_piece:
        gaps.append("stock_qty")
    return gaps
