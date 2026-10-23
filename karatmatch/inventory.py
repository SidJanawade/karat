from __future__ import annotations

from karatmatch.taxonomy import Sku, missing_attributes, price_inr


def gap_report(skus: list[Sku], gold_rate: float) -> list[dict]:
    rows = []
    for sku in skus:
        gaps = missing_attributes(sku)
        if sku.stock_qty == 0:
            gaps.append("out_of_stock")
        if not gaps:
            continue
        rows.append(
            {
                "sku": sku.sku,
                "title": sku.title,
                "gaps": gaps,
                "price_inr": price_inr(sku, gold_rate),
                "vendor_id": sku.vendor_id,
            }
        )
    return rows


def dead_stock(skus: list[Sku], gold_rate: float, max_stock: int = 1) -> list[dict]:
    """Unique / low-qty high-value pieces that should be pushed in the storefront."""
    rows = []
    for sku in skus:
        if sku.stock_qty == 0:
            continue
        if sku.unique_piece or sku.stock_qty <= max_stock:
            rows.append(
                {
                    "sku": sku.sku,
                    "title": sku.title,
                    "stock_qty": sku.stock_qty,
                    "unique_piece": sku.unique_piece,
                    "price_inr": price_inr(sku, gold_rate),
                }
            )
    rows.sort(key=lambda r: -r["price_inr"])
    return rows[:20]
