"""Frozen cheapest-viable policy for matrix v1.0.

The label is a function of capability tags + available_models + this file.
Generators do not invent winners.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "config" / "model_matrix.v1.yaml"

TIER_SLUG = {
    "free": "free",
    "non-frontier-subscription": "non_frontier_sub",
    "frontier-subscription": "frontier_sub",
    "non-frontier-api": "non_frontier_api",
    "frontier-api": "frontier_api",
}

DEPTH_TIER = {"shallow": 1, "medium": 2, "deep": 3}
TOOL_TIER = {"none": 1, "light": 2, "heavy": 3}
STAKES_TIER = {"low": 1, "medium": 2, "high": 3}
CTX_TIER = {"low": 1, "medium": 2, "high": 3}

# Domains that cannot sit on the free lane even when other tags are mild.
ESCALATING_DOMAINS = {
    "vision": 3,
    "multimodal": 3,
    "planning_law": 2,
    "legal": 2,
    "medical": 3,
}


@dataclass(frozen=True)
class Model:
    id: str
    tier_index: int
    tier_name: str
    tier_slug: str
    source: str
    rank: int  # global cheaper-first order


def load_matrix(path: Path = MATRIX_PATH) -> tuple[list[Model], dict[str, Model]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    models: list[Model] = []
    rank = 0
    for tier_index in sorted(raw["tiers"]):
        block = raw["tiers"][tier_index]
        name = block["name"]
        slug = TIER_SLUG[name]
        for item in block["models"]:
            models.append(
                Model(
                    id=item["id"],
                    tier_index=int(tier_index),
                    tier_name=name,
                    tier_slug=slug,
                    source=item["source"],
                    rank=rank,
                )
            )
            rank += 1
    by_id = {m.id: m for m in models}
    return models, by_id


def min_tier_index(capability: dict[str, Any]) -> int:
    needed = max(
        DEPTH_TIER[capability["reasoning_depth"]],
        TOOL_TIER[capability["tool_use"]],
        STAKES_TIER[capability["stakes"]],
        CTX_TIER[capability["context_pressure"]],
    )
    for domain in capability.get("domain") or []:
        needed = max(needed, ESCALATING_DOMAINS.get(domain, 1))
    return needed


def choose(capability: dict[str, Any], available_ids: list[str], by_id: dict[str, Model]) -> Model:
    """Highest-priority (lowest tier, then YAML order) sufficient model."""
    needed = min_tier_index(capability)
    candidates: list[Model] = []
    for mid in available_ids:
        model = by_id.get(mid)
        if model is None:
            raise ValueError(f"unknown model id: {mid}")
        if model.tier_index >= needed:
            candidates.append(model)
    if not candidates:
        raise ValueError("no sufficient model in available_models")
    candidates.sort(key=lambda m: m.rank)
    return candidates[0]


def forced_escalation(capability: dict[str, Any]) -> bool:
    """True when tags themselves push off the free lane."""
    return min_tier_index(capability) >= 2
