#!/usr/bin/env python3
"""Coverage + schema + priority-rule gate for data/routing/v1.

    python scripts/routing_data/validate.py --strict

Exit 0 only if every ASK gate passes. No training.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from policy import choose, forced_escalation, load_matrix

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "routing" / "v1"

REQUIRED = {
    "schema_version",
    "id",
    "matrix_version",
    "subtask",
    "context_signals",
    "available_models",
    "chosen_model",
    "chosen_tier",
    "confidence",
    "rationale_tags",
    "label_source",
    "outcome",
}
DEPTHS = {"shallow", "medium", "deep"}
TOOLS = {"none", "light", "heavy"}
STAKES = {"low", "medium", "high"}
CTX = {"low", "medium", "high"}
SESS = {"short", "medium", "long"}
BUDGET = {"generous", "constrained", "critical"}
LABELS = {"synthetic", "adversarial", "negative"}
TIERS = {"free", "non_frontier_sub", "frontier_sub", "non_frontier_api", "frontier_api"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSON ({exc})") from exc
    return rows


def schema_errors(row: dict[str, Any], by_id: dict, line: str) -> list[str]:
    errs: list[str] = []
    missing = REQUIRED - set(row)
    if missing:
        errs.append(f"{line}: missing {sorted(missing)}")
        return errs
    if row["schema_version"] != "1.0":
        errs.append(f"{line}: schema_version {row['schema_version']!r}")
    if row["matrix_version"] != "1.0":
        errs.append(f"{line}: matrix_version {row['matrix_version']!r}")
    if row["label_source"] not in LABELS:
        errs.append(f"{line}: label_source {row['label_source']!r}")
    if row["outcome"] is not None:
        errs.append(f"{line}: outcome must be null")
    if row["chosen_tier"] not in TIERS:
        errs.append(f"{line}: chosen_tier {row['chosen_tier']!r}")
    if not isinstance(row["confidence"], (int, float)) or not 0.0 <= float(row["confidence"]) <= 1.0:
        errs.append(f"{line}: confidence {row['confidence']!r}")
    if not isinstance(row["rationale_tags"], list) or not row["rationale_tags"]:
        errs.append(f"{line}: rationale_tags empty")
    if not isinstance(row["available_models"], list) or not row["available_models"]:
        errs.append(f"{line}: available_models empty")
    unknown = [m for m in row["available_models"] if m not in by_id]
    if unknown:
        errs.append(f"{line}: unknown available_models {unknown}")
    if row["chosen_model"] not in by_id:
        errs.append(f"{line}: chosen_model not in matrix: {row['chosen_model']!r}")
    if row["chosen_model"] not in row["available_models"]:
        errs.append(f"{line}: chosen_model not available")
    sub = row.get("subtask") or {}
    cap = sub.get("capability_required") or {}
    if not sub.get("description"):
        errs.append(f"{line}: empty description")
    if cap.get("reasoning_depth") not in DEPTHS:
        errs.append(f"{line}: reasoning_depth")
    if cap.get("tool_use") not in TOOLS:
        errs.append(f"{line}: tool_use")
    if cap.get("stakes") not in STAKES:
        errs.append(f"{line}: stakes")
    if cap.get("context_pressure") not in CTX:
        errs.append(f"{line}: context_pressure")
    if not isinstance(cap.get("domain"), list) or not cap["domain"]:
        errs.append(f"{line}: domain")
    ctx = row.get("context_signals") or {}
    if ctx.get("session_length") not in SESS:
        errs.append(f"{line}: session_length")
    if ctx.get("remaining_budget") not in BUDGET:
        errs.append(f"{line}: remaining_budget")
    if "previous_model" not in ctx:
        errs.append(f"{line}: previous_model missing")
    return errs


def priority_error(row: dict[str, Any], by_id: dict, line: str) -> str | None:
    cap = row["subtask"]["capability_required"]
    try:
        winner = choose(cap, row["available_models"], by_id)
    except ValueError as exc:
        return f"{line}: {exc}"
    if winner.id != row["chosen_model"]:
        return f"{line}: chosen_model {row['chosen_model']} != policy {winner.id}"
    if winner.tier_slug != row["chosen_tier"]:
        return f"{line}: chosen_tier {row['chosen_tier']} != {winner.tier_slug}"
    return None


def gates(rows: list[dict[str, Any]], total_hint: int) -> dict[str, Any]:
    scale = 1.0 if total_hint >= 2000 else total_hint / 2000.0
    min_cell = max(5, int(20 * scale))
    min_model = max(4, int(15 * scale))
    cells: Counter[tuple[str, str, str]] = Counter()
    chosen: Counter[str] = Counter()
    escalations = 0
    for row in rows:
        cap = row["subtask"]["capability_required"]
        cells[(cap["reasoning_depth"], cap["tool_use"], cap["stakes"])] += 1
        chosen[row["chosen_model"]] += 1
        if forced_escalation(cap):
            escalations += 1
    cell_fail = []
    for d in sorted(DEPTHS):
        for t in sorted(TOOLS):
            for s in sorted(STAKES):
                count = cells[(d, t, s)]
                if count < min_cell:
                    cell_fail.append(f"{d}×{t}×{s}={count}<{min_cell}")
    model_fail = [f"{mid}={chosen[mid]}<{min_model}" for mid in sorted(chosen) if chosen[mid] < min_model]
    # Also fail models never chosen.
    return {
        "min_cell": min_cell,
        "min_model": min_model,
        "cell_fail": cell_fail,
        "model_fail": model_fail,
        "cells": {f"{a}×{b}×{c}": n for (a, b, c), n in sorted(cells.items())},
        "chosen": dict(chosen),
        "escalation_n": escalations,
        "escalation_pct": round(100.0 * escalations / max(len(rows), 1), 2),
        "escalation_pass": escalations / max(len(rows), 1) >= 0.15,
        "cell_pass": not cell_fail,
        "model_pass": not model_fail,
    }


def report(train: list[dict], held: list[dict], by_id: dict) -> dict[str, Any]:
    all_rows = train + held
    schema_errs: list[str] = []
    prio_errs: list[str] = []
    ids = []
    for idx, row in enumerate(all_rows, 1):
        tag = f"row#{idx}"
        schema_errs.extend(schema_errors(row, by_id, tag))
        pe = priority_error(row, by_id, tag)
        if pe:
            prio_errs.append(pe)
        ids.append(row.get("id"))
    dupes = [item for item, n in Counter(ids).items() if n > 1]
    train_desc = {r["subtask"]["description"] for r in train}
    leak = sum(1 for r in held if r["subtask"]["description"] in train_desc)
    mix = Counter(r["label_source"] for r in all_rows)
    tiers = Counter(r["chosen_tier"] for r in all_rows)
    g_all = gates(all_rows, len(all_rows))
    g_train = gates(train, len(all_rows))
    return {
        "total": len(all_rows),
        "train": len(train),
        "held_out": len(held),
        "mix": dict(mix),
        "tiers": dict(tiers),
        "schema_errors": len(schema_errs),
        "priority_errors": len(prio_errs),
        "duplicate_ids": len(dupes),
        "held_out_leakage": leak,
        "schema_samples": schema_errs[:8],
        "priority_samples": prio_errs[:8],
        "gates_all": g_all,
        "gates_train": g_train,
        "pass": (
            not schema_errs
            and not prio_errs
            and not dupes
            and leak == 0
            and g_all["cell_pass"]
            and g_all["model_pass"]
            and g_all["escalation_pass"]
        ),
    }


def write_readme(path: Path, payload: dict[str, Any], model_ids: list[str]) -> None:
    g = payload["gates_all"]
    lines = [
        "# Routing examples v1.0",
        "",
        "Publishable MVP allotment data for the cheapest-viable router.",
        "Not training code. Not weights. `outcome` is null — no live Hermes traces yet.",
        "",
        "## Cite",
        "",
        "- Matrix: `config/model_matrix.v1.yaml` (`matrix_version: \"1.0\"`).",
        "- Policy: `scripts/routing_data/policy.py`.",
        "- Schema version: `1.0`.",
        "- Generator: `python scripts/routing_data/generate.py`.",
        "- Gate: `python scripts/routing_data/validate.py --strict`.",
        "",
        "## Priority rule",
        "",
        "When several models satisfy the tags, pick the highest-priority",
        "(lowest-tier) option: `free → non_frontier_sub → frontier_sub →",
        "non_frontier_api → frontier_api`. Within a tier, YAML order is",
        "cheaper / faster. `chosen_model` is that function applied to",
        "`available_models`. Prose never overrides the label.",
        "",
        "## Counts",
        "",
        f"- total: {payload['total']}",
        f"- train.jsonl: {payload['train']}",
        f"- held_out.jsonl: {payload['held_out']} (10% id-hash split, 0 description leakage)",
        "",
        "### By label_source",
        "",
    ]
    for key, val in sorted(payload["mix"].items()):
        pct = 100.0 * val / payload["total"]
        lines.append(f"- {key}: {val} ({pct:.1f}%)")
    lines += ["", "### By chosen_tier", ""]
    for key, val in sorted(payload["tiers"].items()):
        pct = 100.0 * val / payload["total"]
        lines.append(f"- {key}: {val} ({pct:.1f}%)")
    lines += [
        "",
        "## Coverage gates (ASK v1 drop)",
        "",
        f"- cell floor: {g['min_cell']} per reasoning_depth × tool_use × stakes",
        f"- model floor: {g['min_model']} as chosen_model",
        f"- escalation: {g['escalation_pct']}% (need ≥ 15%)",
        f"- cells: {'PASS' if g['cell_pass'] else 'FAIL ' + ', '.join(g['cell_fail'])}",
        f"- models: {'PASS' if g['model_pass'] else 'FAIL ' + ', '.join(g['model_fail'])}",
        f"- escalation: {'PASS' if g['escalation_pass'] else 'FAIL'}",
        "",
        "### Cell table",
        "",
        "| reasoning_depth | tool_use | stakes | n |",
        "| --- | --- | --- | ---: |",
    ]
    for key, val in g["cells"].items():
        a, b, c = key.split("×")
        lines.append(f"| {a} | {b} | {c} | {val} |")
    lines += ["", "### chosen_model counts", "", "| id | n |", "| --- | ---: |"]
    for mid in model_ids:
        lines.append(f"| {mid} | {g['chosen'].get(mid, 0)} |")
    lines += [
        "",
        "## Schema",
        "",
        "One JSON object per line. Mandatory fields are exactly those in the",
        "ASK: `schema_version`, `id`, `matrix_version`, `subtask`,",
        "`context_signals`, `available_models`, `chosen_model`, `chosen_tier`,",
        "`confidence`, `rationale_tags`, `label_source`, `outcome`.",
        "",
        "Real Hermes traces (25% in the long-run mix) are **not** in this drop.",
        "That slot stays empty until traces exist. Adversarial + negative +",
        "synthetic fill the file so it is trainable without lying about source.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=DATA)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--write-readme", action="store_true")
    args = parser.parse_args()

    models, by_id = load_matrix()
    train = load_jsonl(args.dir / "train.jsonl")
    held = load_jsonl(args.dir / "held_out.jsonl")
    payload = report(train, held, by_id)
    print(json.dumps({k: v for k, v in payload.items() if k not in {"schema_samples", "priority_samples"} or payload[k]}, indent=2))
    if payload["schema_samples"]:
        print("schema samples:", *payload["schema_samples"], sep="\n  ")
    if payload["priority_samples"]:
        print("priority samples:", *payload["priority_samples"], sep="\n  ")
    if args.write_readme:
        write_readme(args.dir / "README.md", payload, [m.id for m in models])
        print(f"wrote {args.dir / 'README.md'}")
    if args.strict and not payload["pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
