#!/usr/bin/env python3
"""I→T→E chooser on config/matrix.exploded.v1.yaml.

    python scripts/routing_data/policy_nested.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "config" / "matrix.exploded.v1.yaml"

DEPTH = {"shallow": 1, "medium": 2, "deep": 3, "architectural": 4}
TOOLS = {"none": 1, "light": 2, "heavy": 3}
STAKES = {"low": 1, "medium": 2, "high": 3}
CTX = {"low": 1, "medium": 2, "high": 3, "short": 1, "long": 2, "full-history": 3}
DOMAIN_BUMP = {"vision": 3, "multimodal": 3, "medical": 3, "planning_law": 2, "legal": 2}
RMIN = {1: 0.35, 2: 0.50, 3: 0.65, 4: 0.78}


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def unit_cost(item: dict) -> float:
    inn = item.get("in_usd_per_m")
    out = item.get("out_usd_per_m")
    if inn is None and out is None:
        return 9_999.0
    return float(inn or 0.0) + float(out or 0.0)


@dataclass(frozen=True)
class Model:
    id: str
    display: str
    vendor: str
    lane: str
    ability_floor: int
    unit_cost: float
    yaml_rank: int
    tools: bool
    vision: bool
    claim: float
    bench: float
    offset: float
    reality: float


@dataclass(frozen=True)
class Decision:
    model: Model | None
    lane: str | None
    vendor: str | None
    confidence: float
    escalated: bool
    reason: str
    need: int


def load_exploded(path: Path = MATRIX_PATH):
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    alpha = float(raw["alpha"])
    beta = float(raw["beta"])
    models: list[Model] = []
    rank = 0
    for vendor, block in raw["vendors"].items():
        for item in block["models"]:
            claim = float(item["vendor_claim"])
            bench = float(item["bench"])
            offset = float(item["community_offset"])
            # NOTE: alpha + (1-alpha) + beta = 1.25, not 1 -- this is not a
            # true 3-term convex combination. bench/claim are the convex
            # combination (their coefficients do sum to 1); offset is a
            # separate +/-beta correction layered on top, pre-clip. See the
            # long comment on compute_reality() in _build_exploded_matrix.py
            # for why this is intentionally left as-is rather than
            # renormalized (frozen formula; renormalizing would change
            # every reality score and every derived label).
            reality = clip01(alpha * bench + (1.0 - alpha) * claim + beta * offset)
            models.append(
                Model(
                    id=item["id"],
                    display=item.get("display", item["id"]),
                    vendor=vendor,
                    lane=item["lane"],
                    ability_floor=int(item["ability_floor"]),
                    unit_cost=unit_cost(item),
                    yaml_rank=rank,
                    tools=bool(item.get("tools", False)),
                    vision=bool(item.get("vision", False)),
                    claim=claim,
                    bench=bench,
                    offset=offset,
                    reality=reality,
                )
            )
            rank += 1
    return raw, models, {m.id: m for m in models}


def need(tags: dict[str, Any]) -> int:
    n = max(
        DEPTH[tags["reasoning_depth"]],
        TOOLS[tags["tool_use"]],
        STAKES[tags["stakes"]],
        CTX[tags.get("context_pressure", "low")],
    )
    for domain in tags.get("domain") or []:
        n = max(n, DOMAIN_BUMP.get(domain, 1))
    return n


def covers(m: Model, tags: dict[str, Any]) -> bool:
    if TOOLS[tags["tool_use"]] >= 2 and not m.tools:
        return False
    domains = tags.get("domain") or []
    if any(d in {"vision", "multimodal"} for d in domains) and not m.vision:
        return False
    return True


def eligible(models, tags, available, require_reality):
    n = need(tags)
    rmin = RMIN[min(n, 4)]
    want = set(available) if available is not None else None
    out = []
    for m in models:
        if want is not None and m.id not in want:
            continue
        if m.ability_floor < n:
            continue
        if not covers(m, tags):
            continue
        if require_reality and m.reality < rmin:
            continue
        out.append(m)
    return out


def pick_in_lane(pool, lane):
    """Tie-break exactly as frozen in docs/algorithm-phase1.md's T step:
    cheapest unit cost, then higher reality, then YAML declaration order.
    (An undocumented `price_rank` key used to sit between unit_cost and
    reality here — it appeared nowhere in the frozen spec or the source
    matrix data, so it was spec/code drift, not a real tie-break signal.
    Removed 2026-08-27 rather than left silently deciding ties.)
    """
    subset = [m for m in pool if m.lane == lane]
    if not subset:
        return None
    subset.sort(key=lambda m: (m.unit_cost, -m.reality, m.yaml_rank))
    return subset[0]


def choose(tags, available, raw, models):
    lanes = list(raw["lane_order"])
    tau = float(raw["confidence_tau"])
    n = need(tags)
    pool = eligible(models, tags, available, True)
    dropped = False
    if not pool:
        pool = eligible(models, tags, available, False)
        dropped = True
    if not pool:
        return Decision(None, None, None, 0.0, False, "no_sufficient_model", n)
    winner = None
    for lane in lanes:
        winner = pick_in_lane(pool, lane)
        if winner is not None:
            break
    rmin = RMIN[min(n, 4)]
    gamma = winner.reality - rmin
    same = sum(1 for m in pool if m.lane == winner.lane)
    conf = clip01(0.50 + 0.40 * gamma + (0.10 if same >= 2 else 0.0))
    if dropped:
        conf = min(conf, 0.55)
    escalated = False
    reason = "reality_floor_dropped" if dropped else "cheapest_sufficient"
    if conf < tau:
        idx = lanes.index(winner.lane)
        if idx + 1 < len(lanes):
            nxt = pick_in_lane(pool, lanes[idx + 1])
            if nxt is not None:
                winner = nxt
                escalated = True
                reason = "low_conf_one_rung"
                gamma = winner.reality - rmin
                conf = clip01(0.55 + 0.35 * gamma)
    return Decision(winner, winner.lane, winner.vendor, round(conf, 3), escalated, reason, n)


def demo() -> None:
    raw, models, _ = load_exploded()
    cases = [
        {"reasoning_depth": "shallow", "tool_use": "none", "stakes": "low", "context_pressure": "low", "domain": ["code"]},
        {"reasoning_depth": "medium", "tool_use": "light", "stakes": "medium", "context_pressure": "medium", "domain": ["code"]},
        {"reasoning_depth": "deep", "tool_use": "heavy", "stakes": "high", "context_pressure": "high", "domain": ["planning_law"]},
        {"reasoning_depth": "medium", "tool_use": "light", "stakes": "medium", "context_pressure": "medium", "domain": ["vision"]},
    ]
    for tags in cases:
        d = choose(tags, None, raw, models)
        mid = d.model.id if d.model else None
        print(f"need={d.need} {tags['reasoning_depth']}/{tags['tool_use']}/{tags['domain']} -> {d.lane}/{d.vendor}/{mid} conf={d.confidence} {d.reason} esc={d.escalated}")


if __name__ == "__main__":
    raise SystemExit(demo())
