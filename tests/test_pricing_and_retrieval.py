from pathlib import Path

from karatmatch.embeddings import CatalogIndex
from karatmatch.images import render_sku
from karatmatch.nlu import parse_query
from karatmatch.retrieval import Retriever
from karatmatch.seed import build_catalog
from karatmatch.taxonomy import Metal, Purity, Sku, price_inr


def test_22k_price_tracks_gold_rate():
    sku = Sku(
        sku="KM-TEST",
        title="22k gold ring",
        description="test",
        vendor_id="v",
        attributes={
            "category": "ring",
            "style": "minimal",
            "metal": "gold",
            "purity": "22k",
            "gem": "none",
            "occasion": "daily",
            "region": "pan_india",
        },
        weight_grams=4.0,
        making_charge_pct=10.0,
        stone_value_inr=0,
        stock_qty=1,
        image_name="x.jpg",
    )
    p = price_inr(sku, gold_rate_24k=10000)
    metal = 4.0 * 10000 * (22 / 24)
    assert abs(p - (metal * 1.10)) < 0.05


def test_visual_self_match(tmp_path: Path):
    skus = build_catalog(count=36, seed=1)[:12]
    images = tmp_path / "images"
    for sku in skus:
        render_sku(sku, images / sku.image_name)
    index = CatalogIndex.build(skus, images)
    retriever = Retriever(index, gold_rate=9000)
    target = skus[3]
    hits = retriever.match_photo(images / target.image_name, top_k=3)
    assert hits[0].sku.sku == target.sku


def test_budget_filter_rejects_expensive(tmp_path: Path):
    skus = build_catalog(count=40, seed=2)[:20]
    images = tmp_path / "images"
    for sku in skus:
        render_sku(sku, images / sku.image_name)
    retriever = Retriever(CatalogIndex.build(skus, images), gold_rate=9000)
    gold_prices = [price_inr(s, 9000) for s in skus if s.attributes.metal is Metal.GOLD]
    cap = sorted(gold_prices)[len(gold_prices) // 2]
    parsed = parse_query(f"gold under {int(cap)}")
    hits = retriever.search(parsed=parsed, top_k=10)
    assert hits
    assert all(h.price_inr <= cap for h in hits)


def test_purity_enum_roundtrip():
    assert Purity.K22.value == "22k"
    assert Metal.ROSE_GOLD.value == "rose_gold"
