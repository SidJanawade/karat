from __future__ import annotations

import re
from dataclasses import dataclass

from karatmatch.taxonomy import ALIAS_RULES, Filters


_BUDGET = re.compile(
    r"(?:under|below|upto|up to|less than|<)\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]*)",
    re.I,
)
_LAKH = re.compile(r"(?:under|below|upto|up to)\s*(\d+(?:\.\d+)?)\s*lakh", re.I)


@dataclass(frozen=True)
class ParsedQuery:
    text: str
    filters: Filters
    tokens: list[str]


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1]


def parse_query(text: str) -> ParsedQuery:
    lowered = text.lower()
    kwargs: dict = {}
    # Longest phrase first so "rose gold" wins over "gold".
    for alias, field, value in sorted(ALIAS_RULES, key=lambda row: -len(row[0])):
        if alias in lowered and field not in kwargs:
            kwargs[field] = value

    max_price = None
    lakh = _LAKH.search(lowered)
    if lakh:
        max_price = float(lakh.group(1)) * 100_000
    else:
        m = _BUDGET.search(lowered)
        if m:
            max_price = float(m.group(1).replace(",", ""))

    filters = Filters(max_price_inr=max_price, **kwargs)
    return ParsedQuery(text=text, filters=filters, tokens=tokenize(text))


def extract_from_title(title: str) -> dict[str, str]:
    """Weak labeler used for enrichment evals — same alias table as NLU."""
    parsed = parse_query(title)
    data = parsed.filters.model_dump(exclude_none=True)
    data.pop("max_price_inr", None)
    data.pop("in_stock_only", None)
    return {k: str(v) for k, v in data.items()}
