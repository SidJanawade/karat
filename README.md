# KaratMatch

Multimodal jewellery catalog intelligence: **shop-by-photo**, **vernacular + budget search**, **SKU duplicate detection**, and **India-style metal + making quotes**.

This is the domain system that is missing from a generic RAG portfolio. Jewellers do not lose sales because they lack a chatbot. They lose them because a customer sends a WhatsApp photo, the catalogue has three near-identical vendor SKUs, and the listing is missing purity, weight, or occasion.

KaratMatch treats that as a retrieval + taxonomy problem, not a prompt.

## Why this architecture

Jewellery search is **fine-grained**. Two 22K temple jhumkas can share metal colour and still differ in motif, drop length, and stone family. Generic CLIP demos rank “gold thing” well and “this design vs that design” poorly.

The production-shaped split:

| Layer | Job |
| --- | --- |
| Taxonomy | Shared contract for NLU, enrichment, filters, and evals |
| Visual encoder | Swap-out interface (`visual_vector`). Default: HSV + edges so CI runs with no GPU. Replace with SigLIP/CLIP later without touching retrieval. |
| Lexical | BM25 on title/description |
| Fusion | Reciprocal rank fusion + hard attribute/budget filters |
| Ops | Duplicate pairs, listing gaps, quote desk |

E-commerce, inventory, CX, and ops share **one index**. That is the point.

## Quick start

Python 3.11+.

```powershell
cd C:\Users\janaw\KaratMatch
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m karatmatch.seed
python -m karatmatch.evals
uvicorn karatmatch.api:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Try:

- `22k gold temple jhumkas under 25000 for wedding`
- Boutique → Photo → upload any generated plate from `data/images/`
- Atelier ops → duplicates, listing gaps, quote desk

## API

| Method | Path | Use |
| --- | --- | --- |
| GET | `/health` | Liveness + gold rate |
| GET | `/catalog` | Paginated SKUs |
| POST | `/search` | Text and/or image, NLU filters |
| POST | `/inventory/match` | Counter photo → SKU |
| GET | `/inventory/duplicates` | Near-duplicate listings |
| GET | `/inventory/gaps` | Incomplete / OOS listings |
| POST | `/quote` | Weight × rate × purity + making |
| GET | `/metrics` | Last eval report |

## Eval harness (quality gate)

`python -m karatmatch.evals` writes `data/eval_report.json`:

- visual Recall@5 (photo of a SKU finds itself)
- hybrid text Recall@8 vs text-only ablation (filters dropped)
- duplicate-pair recall
- title → attribute accuracy
- budget-filter accuracy
- p50 / p99 match latency

GitHub Actions fails the PR if visual recall drops or hybrid does not beat the ablation.

## Honest limits (say this in interviews)

- Seed images are **controlled product plates**, not studio photography. They exist so retrieval and evals are deterministic on a laptop. Swap `visual_vector()` for SigLIP on a real catalogue.
- The system **does not certify diamonds, hallmarks, or purity**. It matches catalogue identity and estimates metal + making.
- Gold rate is a config value (`KARATMATCH_GOLD_RATE_24K_INR`), not a live MCX feed.

## Resume bullets

KaratMatch: Multimodal Jewellery Catalog Intelligence | Python, FastAPI, NumPy, eval harness, Docker

- Built a jewellery-specific retrieval stack that fuses visual embeddings, BM25, and a constrained taxonomy (metal, purity, style, occasion) with reciprocal rank fusion and hard budget filters.
- Implemented inventory matching: photo → SKU, near-duplicate vendor listings, and listing-gap reports that flag missing attributes and stock holes.
- Added an India-style quote engine (24K rate × purity factor × weight + making % + stone value) with an explicit GST/certification disclaimer.
- Shipped an evaluation harness (Recall@k, duplicate recall, attribute accuracy, p50/p99) as a CI quality gate, with a hybrid vs text-only ablation.

## Project layout

```
karatmatch/
  taxonomy.py      # canonical jewellery schema
  nlu.py           # “22k temple jhumkas under 25k”
  embeddings.py    # visual + attribute vectors, swap point for CLIP
  retrieval.py     # BM25 + RRF + filters
  inventory.py     # gaps, dead stock
  seed.py          # 220+ SKU synthetic but structured catalogue
  evals.py         # quality gate
  api.py           # FastAPI
  static/          # boutique + atelier UI
```
