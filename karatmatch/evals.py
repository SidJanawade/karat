from __future__ import annotations

import json
import time
from karatmatch.config import settings
from karatmatch.embeddings import CatalogIndex
from karatmatch.nlu import extract_from_title, parse_query
from karatmatch.retrieval import Retriever
from karatmatch.seed import load_skus
from karatmatch.taxonomy import price_inr


def _recall_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    return float(any(sku in relevant for sku in ranked_ids[:k]))


def run_evals(retriever: Retriever) -> dict:
    skus = retriever.index.skus
    images = settings.images_dir
    gold = retriever.gold_rate

    visual_hits: list[float] = []
    visual_lat: list[float] = []
    for sku in skus[:40]:
        t0 = time.perf_counter()
        hits = retriever.match_photo(images / sku.image_name, top_k=5)
        visual_lat.append((time.perf_counter() - t0) * 1000)
        visual_hits.append(_recall_at_k([h.sku.sku for h in hits], {sku.sku}, 5))

    text_hits: list[float] = []
    text_only_hits: list[float] = []
    for sku in skus[10:50]:
        query = f"{sku.attributes.purity.value} {sku.attributes.metal.value.replace('_', ' ')} {sku.attributes.style.value} {sku.attributes.category.value.replace('_', ' ')}"
        parsed = parse_query(query)
        hits = retriever.search(parsed=parsed, top_k=8)
        text_hits.append(_recall_at_k([h.sku.sku for h in hits], {sku.sku}, 8))
        # Ablation: drop structured filters, keep BM25+RRF only.
        parsed_nofilt = parse_query(query)
        parsed_nofilt = parsed_nofilt.__class__(
            text=parsed_nofilt.text,
            tokens=parsed_nofilt.tokens,
            filters=parsed_nofilt.filters.model_copy(
                update={
                    "category": None,
                    "style": None,
                    "metal": None,
                    "purity": None,
                    "gem": None,
                    "occasion": None,
                    "region": None,
                }
            ),
        )
        loose = retriever.search(parsed=parsed_nofilt, top_k=8)
        text_only_hits.append(_recall_at_k([h.sku.sku for h in loose], {sku.sku}, 8))

    dup_truth = {(s.duplicate_of, s.sku) for s in skus if s.duplicate_of}
    predicted = {(a.sku, b.sku) for a, b, _ in retriever.duplicates(threshold=0.97)}
    predicted |= {(b, a) for a, b in list(predicted)}
    tp = sum(1 for a, b in dup_truth if (a, b) in predicted or (b, a) in predicted)
    dup_recall = tp / max(len(dup_truth), 1)

    attr_correct = 0
    attr_total = 0
    for sku in skus[:80]:
        extracted = extract_from_title(sku.title)
        truth = sku.attributes.model_dump()
        for key in ("category", "metal", "purity", "style"):
            attr_total += 1
            if extracted.get(key) == str(truth[key]):
                attr_correct += 1

    budget_ok = 0
    budget_n = 0
    for sku in skus[20:40]:
        price = price_inr(sku, gold)
        cap = price + 500
        parsed = parse_query(f"{sku.attributes.category.value} under {int(cap)}")
        hits = retriever.search(parsed=parsed, top_k=12)
        budget_n += 1
        if hits and all(h.price_inr <= cap + 1 for h in hits):
            budget_ok += 1

    visual_lat.sort()

    def pct(xs: list[float], p: float) -> float:
        if not xs:
            return 0.0
        idx = min(int(round((p / 100) * (len(xs) - 1))), len(xs) - 1)
        return round(xs[idx], 2)

    report = {
        "n_skus": len(skus),
        "visual_recall_at_5": round(sum(visual_hits) / max(len(visual_hits), 1), 3),
        "hybrid_text_recall_at_8": round(sum(text_hits) / max(len(text_hits), 1), 3),
        "text_only_recall_at_8": round(sum(text_only_hits) / max(len(text_only_hits), 1), 3),
        "duplicate_recall": round(dup_recall, 3),
        "attribute_title_accuracy": round(attr_correct / max(attr_total, 1), 3),
        "budget_filter_accuracy": round(budget_ok / max(budget_n, 1), 3),
        "visual_match_p50_ms": pct(visual_lat, 50),
        "visual_match_p99_ms": pct(visual_lat, 99),
        "notes": [
            "Visual plates are deterministic stand-ins for studio shots; swap visual_vector() for SigLIP.",
            "Hybrid text uses NLU filters + BM25 + RRF. text_only drops structured filters.",
            "Do not claim gemological authenticity. This system matches catalogue identity.",
        ],
    }
    settings.eval_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    if not settings.catalog_path.exists():
        raise SystemExit("Run `python -m karatmatch.seed` first.")
    skus = load_skus()
    index = CatalogIndex.build(skus, settings.images_dir)
    retriever = Retriever(index, settings.gold_rate_24k_inr)
    report = run_evals(retriever)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
