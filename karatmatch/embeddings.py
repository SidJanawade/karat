from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from karatmatch.taxonomy import Category, Gem, Metal, Occasion, Purity, Region, Sku, Style

_CATS = list(Category)
_STYLES = list(Style)
_METALS = list(Metal)
_PURITIES = list(Purity)
_GEMS = list(Gem)
_OCC = list(Occasion)
_REG = list(Region)


def _onehot(options: list, value) -> np.ndarray:
    vec = np.zeros(len(options), dtype=np.float32)
    vec[options.index(value)] = 1.0
    return vec


def attribute_vector(sku: Sku) -> np.ndarray:
    parts = [
        _onehot(_CATS, sku.attributes.category),
        _onehot(_STYLES, sku.attributes.style),
        _onehot(_METALS, sku.attributes.metal),
        _onehot(_PURITIES, sku.attributes.purity),
        _onehot(_GEMS, sku.attributes.gem),
        _onehot(_OCC, sku.attributes.occasion),
        _onehot(_REG, sku.attributes.region),
    ]
    return np.concatenate(parts)


def visual_vector(image_path: Path, bins: int = 8) -> np.ndarray:
    """HSV histogram + edge energy. Swap this for SigLIP/CLIP without changing retrieval."""
    img = Image.open(image_path).convert("RGB").resize((128, 128))
    hsv = np.asarray(img.convert("HSV"), dtype=np.float32)
    hist, _ = np.histogramdd(
        hsv.reshape(-1, 3),
        bins=(bins, bins, 4),
        range=((0, 255), (0, 255), (0, 255)),
    )
    hist = hist.astype(np.float32).ravel()
    hist /= hist.sum() + 1e-8
    gray = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    gx = np.abs(np.diff(gray, axis=1)).mean()
    gy = np.abs(np.diff(gray, axis=0)).mean()
    return np.concatenate([hist, np.array([gx, gy], dtype=np.float32)])


def l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    return mat / np.clip(norms, 1e-8, None)


class CatalogIndex:
    def __init__(self, skus: list[Sku], visual: np.ndarray, attributes: np.ndarray):
        self.skus = skus
        self.sku_ids = [s.sku for s in skus]
        self.visual = l2_normalize(visual.astype(np.float32))
        self.attributes = l2_normalize(attributes.astype(np.float32))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            visual=self.visual,
            attributes=self.attributes,
            sku_ids=np.array(self.sku_ids),
        )

    @classmethod
    def build(cls, skus: list[Sku], images_dir: Path) -> CatalogIndex:
        visual = np.stack([visual_vector(images_dir / s.image_name) for s in skus])
        attributes = np.stack([attribute_vector(s) for s in skus])
        return cls(skus, visual, attributes)
