from __future__ import annotations

import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from karatmatch import __version__
from karatmatch.config import settings
from karatmatch.embeddings import CatalogIndex
from karatmatch.inventory import dead_stock, gap_report
from karatmatch.nlu import parse_query
from karatmatch.retrieval import Retriever
from karatmatch.seed import load_skus
from karatmatch.taxonomy import Filters, Metal, Purity, Sku, price_inr

STATIC_DIR = Path(__file__).parent / "static"


class AppState:
    retriever: Retriever
    skus: list[Sku]


state = AppState()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.catalog_path.exists():
        from karatmatch.seed import build_catalog, persist

        persist(build_catalog())
    skus = load_skus()
    index = CatalogIndex.build(skus, settings.images_dir)
    state.skus = skus
    state.retriever = Retriever(index, settings.gold_rate_24k_inr)
    yield


app = FastAPI(
    title="KaratMatch",
    description="Multimodal jewellery catalog intelligence",
    version=__version__,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuoteRequest(BaseModel):
    weight_grams: float = Field(gt=0)
    metal: Metal = Metal.GOLD
    purity: Purity = Purity.K22
    making_charge_pct: float = 12.0
    stone_value_inr: float = 0.0


def _hit_payload(hit) -> dict:
    s = hit.sku
    return {
        "sku": s.sku,
        "title": s.title,
        "description": s.description,
        "vendor_id": s.vendor_id,
        "attributes": s.attributes.model_dump(),
        "weight_grams": s.weight_grams,
        "stock_qty": s.stock_qty,
        "unique_piece": s.unique_piece,
        "price_inr": hit.price_inr,
        "score": round(hit.score, 5),
        "reasons": hit.reasons,
        "image_url": f"/media/{s.image_name}",
    }


def _sku_payload(sku: Sku) -> dict:
    return {
        "sku": sku.sku,
        "title": sku.title,
        "description": sku.description,
        "vendor_id": sku.vendor_id,
        "attributes": sku.attributes.model_dump(),
        "weight_grams": sku.weight_grams,
        "stock_qty": sku.stock_qty,
        "unique_piece": sku.unique_piece,
        "price_inr": price_inr(sku, settings.gold_rate_24k_inr),
        "image_url": f"/media/{sku.image_name}",
        "duplicate_of": sku.duplicate_of,
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "skus": len(getattr(state, "skus", []) or []),
        "gold_rate_24k_inr": settings.gold_rate_24k_inr,
    }


@app.get("/catalog")
def catalog(limit: int = 48, offset: int = 0) -> dict:
    rows = state.skus[offset : offset + limit]
    return {"total": len(state.skus), "items": [_sku_payload(s) for s in rows]}


@app.get("/catalog/{sku_id}")
def catalog_item(sku_id: str) -> dict:
    sku = next((s for s in state.skus if s.sku == sku_id), None)
    if sku is None:
        raise HTTPException(404, "unknown SKU")
    return _sku_payload(sku)


@app.post("/search")
async def search(
    q: str = Form(""),
    top_k: int = Form(8),
    in_stock_only: bool = Form(False),
    image: UploadFile | None = File(None),
) -> dict:
    parsed = parse_query(q) if q.strip() else None
    if parsed is not None:
        parsed = parsed.__class__(
            text=parsed.text,
            tokens=parsed.tokens,
            filters=parsed.filters.model_copy(update={"in_stock_only": in_stock_only}),
        )
    filters = parsed.filters if parsed else Filters(in_stock_only=in_stock_only)
    tmp: Path | None = None
    if image is not None and image.filename:
        suffix = Path(image.filename).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(await image.read())
            tmp = Path(handle.name)
    hits = state.retriever.search(parsed=parsed, image_path=tmp, filters=filters, top_k=top_k)
    if tmp is not None:
        tmp.unlink(missing_ok=True)
    return {
        "query": q,
        "filters": filters.model_dump(),
        "results": [_hit_payload(h) for h in hits],
    }


@app.post("/inventory/match")
async def inventory_match(image: UploadFile = File(...), top_k: int = Form(5)) -> dict:
    suffix = Path(image.filename or "query.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(await image.read())
        tmp = Path(handle.name)
    hits = state.retriever.match_photo(tmp, top_k=top_k)
    tmp.unlink(missing_ok=True)
    return {"results": [_hit_payload(h) for h in hits]}


@app.get("/inventory/gaps")
def inventory_gaps() -> dict:
    return {"items": gap_report(state.skus, settings.gold_rate_24k_inr)}


@app.get("/inventory/duplicates")
def inventory_duplicates() -> dict:
    pairs = state.retriever.duplicates()
    return {
        "items": [
            {
                "left": _sku_payload(a),
                "right": _sku_payload(b),
                "similarity": round(score, 4),
            }
            for a, b, score in pairs[:20]
        ]
    }


@app.get("/inventory/push")
def inventory_push() -> dict:
    return {"items": dead_stock(state.skus, settings.gold_rate_24k_inr)}


@app.post("/quote")
def quote(req: QuoteRequest) -> dict:
    metal_is_gold = req.metal in {Metal.GOLD, Metal.ROSE_GOLD, Metal.WHITE_GOLD}
    from karatmatch.taxonomy import PURITY_FINE

    if metal_is_gold:
        metal_value = req.weight_grams * settings.gold_rate_24k_inr * PURITY_FINE[req.purity]
    elif req.metal is Metal.SILVER:
        metal_value = req.weight_grams * 110.0
    else:
        metal_value = req.weight_grams * 3200.0
    making = metal_value * (req.making_charge_pct / 100.0)
    total = round(metal_value + making + req.stone_value_inr, 2)
    return {
        "metal_value_inr": round(metal_value, 2),
        "making_inr": round(making, 2),
        "stone_value_inr": req.stone_value_inr,
        "total_inr": total,
        "gold_rate_24k_inr": settings.gold_rate_24k_inr,
        "disclaimer": "Estimate excluding GST, hallmarking, and certification. Not a bullion quote.",
    }


@app.get("/metrics")
def metrics() -> dict:
    path = settings.eval_path
    if not path.exists():
        return {"eval_report": None}
    import json

    return {"eval_report": json.loads(path.read_text(encoding="utf-8"))}


@app.get("/media/{name}")
def media(name: str):
    path = (settings.images_dir / name).resolve()
    if not str(path).startswith(str(settings.images_dir.resolve())) or not path.exists():
        raise HTTPException(404)
    return FileResponse(path)


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
