from karatmatch.nlu import parse_query
from karatmatch.taxonomy import Category, Metal, Purity, Style


def test_parses_indian_jewellery_query():
    parsed = parse_query("22k gold temple jhumkas under 25000 for wedding")
    assert parsed.filters.purity is Purity.K22
    assert parsed.filters.metal is Metal.GOLD
    assert parsed.filters.style is Style.TEMPLE
    assert parsed.filters.category is Category.EARRING
    assert parsed.filters.max_price_inr == 25000


def test_rose_gold_not_yellow_gold():
    parsed = parse_query("rose gold minimal ring")
    assert parsed.filters.metal is Metal.ROSE_GOLD
    assert parsed.filters.category is Category.RING
