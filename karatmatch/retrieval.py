from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from karatmatch.embeddings import CatalogIndex, l2_normalize, visual_vector
from karatmatch.nlu import ParsedQuery, tokenize
from karatmatch.taxonomy import Filters, Sku, price_inr


def _idf(df: int, n: int) -> float:
    return math.log(1 + (n - df + 0.5) / (df + 0.5))


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs = docs
        self.n = len(docs)
        self.avgdl = sum(len(d) for d in docs) / max(self.n, 1)
        df: dict[str, int] = defaultdict(int)
        for doc in docs:
            for term in set(doc):
                df[term] += 1
        self.idf = {t: _idf(c, self.n) for t, c in df.items()}

    def scores(self, query: list[str]) -> np.ndarray:
        out = np.zeros(self.n, dtype=np.float32)
        for i, doc in enumerate(self.docs):
            if not doc:
                continue
            tf: dict[str, int] = defaultdict(int)
            for t in doc:
                tf[t] += 1
            dl = len(doc)
            score = 0.0
            for term in query:
                if term not in tf:
                    continue
                freq = tf[term]
                denom = freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += self.idf.get(term, 0.0) * (freq * (self.k1 + 1) / denom)
            out[i] = score
        return out


def rrf(rank_lists: list[list[int]], k: int = 60) -> np.ndarray:
    n = 0
    for ranks in rank_lists:
        n = max(n, max(ranks) + 1 if ranks else 0)
    scores = np.zeros(n, dtype=np.float32)
    for ranks in rank_lists:
        for rank, idx in enumerate(ranks):
            scores[idx] += 1.0 / (k + rank + 1)
    return scores


@dataclass
class Hit:
    sku: Sku
    score: float
    price_inr: float
    reasons: list[str]


class Retriever:
    def __init__(self, index: CatalogIndex, gold_rate: float):
        self.index = index
        self.gold_rate = gold_rate
        docs = [tokenize(s.title + " " + s.description) for s in index.skus]
        self.bm25 = BM25(docs)

    def search(
        self,
        parsed: ParsedQuery | None = None,
        image_path: Path | None = None,
        filters: Filters | None = None,
        top_k: int = 8,
    ) -> list[Hit]:
        filters = filters or (parsed.filters if parsed else Filters())
        n = len(self.index.skus)
        visual_scores = np.zeros(n, dtype=np.float32)
        text_scores = np.zeros(n, dtype=np.float32)

        if image_path is not None:
            q = l2_normalize(visual_vector(image_path)[None, :])[0]
            visual_scores = self.index.visual @ q
        if parsed is not None and parsed.tokens:
            text_scores = self.bm25.scores(parsed.tokens)

        rank_lists: list[list[int]] = []
        if image_path is not None:
            rank_lists.append(list(np.argsort(-visual_scores)))
        if parsed is not None and parsed.tokens:
            rank_lists.append(list(np.argsort(-text_scores)))
        if not rank_lists:
            fused_bias = self.index.attributes.sum(axis=1)
            rank_lists.append(list(np.argsort(-fused_bias)))

        fused = rrf(rank_lists)
        eligible = []
        prices = []
        for i, sku in enumerate(self.index.skus):
            price = price_inr(sku, self.gold_rate)
            prices.append(price)
            if not sku.matches(filters):
                continue
            if filters.max_price_inr is not None and price > filters.max_price_inr:
                continue
            fused[i] += sku.soft_boost(filters)
            eligible.append(i)

        if not eligible:
            return []

        order = sorted(eligible, key=lambda i: fused[i], reverse=True)[:top_k]
        hits: list[Hit] = []
        for i in order:
            sku = self.index.skus[i]
            reasons = []
            if image_path is not None:
                reasons.append(f"visual={visual_scores[i]:.3f}")
            if parsed is not None and parsed.tokens:
                reasons.append(f"text={text_scores[i]:.3f}")
            reasons.append(f"rrf={fused[i]:.4f}")
            hits.append(Hit(sku=sku, score=float(fused[i]), price_inr=prices[i], reasons=reasons))
        return hits

    def duplicates(self, threshold: float = 0.97) -> list[tuple[Sku, Sku, float]]:
        sim = self.index.visual @ self.index.visual.T
        pairs: list[tuple[Sku, Sku, float]] = []
        n = len(self.index.skus)
        for i in range(n):
            for j in range(i + 1, n):
                score = float(sim[i, j])
                if score >= threshold:
                    pairs.append((self.index.skus[i], self.index.skus[j], score))
        pairs.sort(key=lambda p: -p[2])
        return pairs

    def match_photo(self, image_path: Path, top_k: int = 5) -> list[Hit]:
        return self.search(image_path=image_path, top_k=top_k)
