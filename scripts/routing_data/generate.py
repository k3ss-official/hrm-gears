#!/usr/bin/env python3
"""Emit schema-valid routing JSONL. Labels come from policy.py, not from prose.

    python scripts/routing_data/generate.py --n 3000

Does not train anything. Does not touch weights.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from policy import Model, choose, forced_escalation, load_matrix, min_tier_index
from templates import ADVERSARIAL, DOMAINS, FILL, NEGATIVE, SYNTHETIC

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "routing" / "v1"
NS = uuid.UUID("8c1d2a70-5b3e-4f91-9c4a-6e2b17d0a8f3")

DEPTHS = ("shallow", "medium", "deep")
TOOLS = ("none", "light", "heavy")
STAKES = ("low", "medium", "high")
CTX = ("low", "medium", "high")
SESS = ("short", "medium", "long")
BUDGET = ("generous", "constrained", "critical")
DOMAIN_KEYS = tuple(DOMAINS.keys())


def fill(template: str, i: int) -> str:
    values = {key: bank[i % len(bank)] for key, bank in FILL.items()}
    return template.format(**values)


def make_id(*parts: object) -> str:
    return str(uuid.uuid5(NS, "|".join(str(p) for p in parts)))


def confidence(label: str, i: int) -> float:
    base = {"synthetic": 0.84, "adversarial": 0.76, "negative": 0.88}[label]
    return round(min(0.97, base + ((i * 17) % 11) / 200.0), 3)


def rationale(model: Model, capability: dict, label: str, escalated: bool) -> list[str]:
    tags = [
        f"tier:{model.tier_slug}",
        f"source:{model.source.replace(' ', '_').lower()}",
        f"depth:{capability['reasoning_depth']}",
        f"tools:{capability['tool_use']}",
        f"stakes:{capability['stakes']}",
    ]
    if escalated:
        tags.append("forced_tier_escalation")
    if label == "adversarial":
        tags.append("looks_simple_but_tags_escalate")
    if label == "negative":
        tags.append("do_not_over_escalate")
        tags.append("cheapest_sufficient")
    else:
        tags.append("cheapest_sufficient")
    if "vision" in capability["domain"] or "multimodal" in capability["domain"]:
        tags.append("needs_multimodal")
    if "planning_law" in capability["domain"] or "legal" in capability["domain"]:
        tags.append("elevated_domain")
    return tags


def example(
    *,
    i: int,
    description: str,
    capability: dict,
    available: list[str],
    label: str,
    models_by_id: dict[str, Model],
    session_i: int,
) -> dict:
    winner = choose(capability, available, models_by_id)
    escalated = forced_escalation(capability)
    return {
        "schema_version": "1.0",
        "id": make_id(i, label, winner.id, description),
        "matrix_version": "1.0",
        "subtask": {
            "description": description,
            "capability_required": capability,
        },
        "context_signals": {
            "session_length": SESS[session_i % 3],
            "remaining_budget": BUDGET[session_i % 3],
            "previous_model": None,
        },
        "available_models": available,
        "chosen_model": winner.id,
        "chosen_tier": winner.tier_slug,
        "confidence": confidence(label, i),
        "rationale_tags": rationale(winner, capability, label, escalated),
        "label_source": label,
        "outcome": None,
    }


def combo_capability(d: str, t: str, s: str, c: str, domain_key: str) -> dict:
    return {
        "reasoning_depth": d,
        "tool_use": t,
        "context_pressure": c,
        "domain": list(DOMAINS[domain_key]),
        "stakes": s,
    }


def generate(n: int, models: list[Model], by_id: dict[str, Model]) -> list[dict]:
    all_ids = [m.id for m in models]
    rows: list[dict] = []
    i = 0

    # Combinatorial synthetic: every depth × tool × stakes cell, many times.
    for cycle in range(8):
        for d in DEPTHS:
            for t in TOOLS:
                for s in STAKES:
                    templates = SYNTHETIC[(d, t, s)]
                    ctx = CTX[cycle % 3]
                    domain_key = DOMAIN_KEYS[(cycle + i) % len(DOMAIN_KEYS)]
                    # Vision domains force tier 3 — keep them off shallow-none-low
                    # cells unless we want escalation (adversarial handles that).
                    if domain_key in {"vision", "planning_law", "legal", "medical"} and d == "shallow" and s == "low":
                        domain_key = "code"
                    cap = combo_capability(d, t, s, ctx, domain_key)
                    desc = f"{fill(templates[cycle % len(templates)], i)} [syn {i}]"
                    # Mostly full availability so cheapest sufficient wins.
                    available = list(all_ids)
                    rows.append(
                        example(
                            i=i,
                            description=desc,
                            capability=cap,
                            available=available,
                            label="synthetic",
                            models_by_id=by_id,
                            session_i=i,
                        )
                    )
                    i += 1

    # Availability masks so every matrix id is the winner ≥ N times.
    per_model = 24
    for model in models:
        cheaper = [m.id for m in models if m.rank < model.rank]
        available = [m.id for m in models if m.rank >= model.rank]
        for k in range(per_model):
            # Tags the winner can actually satisfy.
            if model.tier_index == 1:
                d, t, s, c = "shallow", "none", "low", "low"
            elif model.tier_index == 2:
                d, t, s, c = "medium", "light", "medium", "medium"
            elif model.tier_index == 3:
                d, t, s, c = "deep", "heavy", "high", "high"
            elif model.tier_index == 4:
                d, t, s, c = "deep", "heavy", "high", "high"
            else:
                d, t, s, c = "deep", "heavy", "high", "high"
            domain_key = DOMAIN_KEYS[k % len(DOMAIN_KEYS)]
            if model.tier_index < 3 and domain_key in {"vision"}:
                domain_key = "code"
            cap = combo_capability(d, t, s, c, domain_key)
            # Guarantee sufficiency: if policy would skip this model, drop extra domains.
            while min_tier_index(cap) > model.tier_index:
                cap["domain"] = ["code"]
                cap["reasoning_depth"] = "shallow" if model.tier_index == 1 else cap["reasoning_depth"]
                cap["tool_use"] = "none" if model.tier_index == 1 else cap["tool_use"]
                cap["stakes"] = "low" if model.tier_index == 1 else cap["stakes"]
                cap["context_pressure"] = "low" if model.tier_index == 1 else cap["context_pressure"]
                if min_tier_index(cap) > model.tier_index:
                    break
            templates = SYNTHETIC[
                (cap["reasoning_depth"], cap["tool_use"], cap["stakes"])
            ]
            desc = fill(templates[k % len(templates)], i) + f" [availability mask {model.id} #{k}]"
            rows.append(
                example(
                    i=i,
                    description=desc,
                    capability=cap,
                    available=available,
                    label="synthetic",
                    models_by_id=by_id,
                    session_i=i + k,
                )
            )
            i += 1
            _ = cheaper  # documented: omitted cheaper models are the point

    # Adversarial: cheap-sounding prose, escalating tags.
    adv_n = max(int(n * 0.16), 400)
    adv_combos = [
        ("deep", "heavy", "high", "high", "planning_law"),
        ("deep", "light", "high", "high", "legal"),
        ("medium", "heavy", "high", "medium", "code"),
        ("deep", "none", "high", "high", "medical"),
        ("medium", "light", "high", "high", "ops"),
        ("deep", "heavy", "medium", "high", "vision"),
    ]
    for k in range(adv_n):
        d, t, s, c, domain_key = adv_combos[k % len(adv_combos)]
        cap = combo_capability(d, t, s, c, domain_key)
        desc = f"{fill(ADVERSARIAL[k % len(ADVERSARIAL)], i)} [adv {k}]"
        rows.append(
            example(
                i=i,
                description=desc,
                capability=cap,
                available=list(all_ids),
                label="adversarial",
                models_by_id=by_id,
                session_i=i,
            )
        )
        i += 1

    # Negatives: heroic prose, cheap tags. Correct label is still cheapest sufficient.
    neg_n = max(int(n * 0.07), 180)
    for k in range(neg_n):
        cap = combo_capability("shallow", "none", "low", "low", "code")
        desc = f"{fill(NEGATIVE[k % len(NEGATIVE)], i)} [neg {k}]"
        rows.append(
            example(
                i=i,
                description=desc,
                capability=cap,
                available=list(all_ids),
                label="negative",
                models_by_id=by_id,
                session_i=i,
            )
        )
        i += 1

    # Fill remaining combinatorial variants until we hit n (or just over).
    cycle = 0
    while len(rows) < n:
        d = DEPTHS[cycle % 3]
        t = TOOLS[(cycle // 3) % 3]
        s = STAKES[(cycle // 9) % 3]
        c = CTX[(cycle // 27) % 3]
        domain_key = DOMAIN_KEYS[cycle % len(DOMAIN_KEYS)]
        if domain_key in {"vision", "planning_law", "legal"} and d == "shallow" and s == "low":
            domain_key = "synthesis"
        cap = combo_capability(d, t, s, c, domain_key)
        templates = SYNTHETIC[(d, t, s)]
        desc = fill(templates[cycle % len(templates)], i) + f" (fill {cycle})"
        # Occasional mid-list availability so mid-tier ids keep showing up.
        cut = cycle % len(all_ids)
        available = all_ids[cut:]
        # Keep at least one sufficient model.
        needed = min_tier_index(cap)
        if not any(by_id[mid].tier_index >= needed for mid in available):
            available = list(all_ids)
        rows.append(
            example(
                i=i,
                description=desc,
                capability=cap,
                available=available,
                label="synthetic",
                models_by_id=by_id,
                session_i=i,
            )
        )
        i += 1
        cycle += 1

    # Stable order by id, then split 90/10 without description leakage.
    rows.sort(key=lambda r: r["id"])
    seen_desc: set[str] = set()
    unique: list[dict] = []
    for row in rows:
        desc = row["subtask"]["description"]
        if desc in seen_desc:
            continue
        seen_desc.add(desc)
        unique.append(row)
    return unique


def split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    train, held = [], []
    for row in rows:
        bucket = int(row["id"].replace("-", "")[:8], 16) % 10
        if bucket == 0:
            held.append(row)
        else:
            train.append(row)
    return train, held


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=3000)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    models, by_id = load_matrix()
    rows = generate(args.n, models, by_id)
    train, held = split(rows)
    write_jsonl(args.out / "train.jsonl", train)
    write_jsonl(args.out / "held_out.jsonl", held)

    mix = Counter(r["label_source"] for r in rows)
    tiers = Counter(r["chosen_tier"] for r in rows)
    print(f"total={len(rows)} train={len(train)} held_out={len(held)}")
    print("mix", dict(mix))
    print("tiers", dict(tiers))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
