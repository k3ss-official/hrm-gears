#!/usr/bin/env python3
"""v0 routing trainer — JSONL labels, no HRM weights.

Trains a hashed-tag linear model: capability + available_models → chosen_model.
Purpose: prove the data contract and get a held-out number before we spend T4
hours on a z_H head.

    python scripts/kaggle/train_routing.py
    python scripts/kaggle/train_routing.py --epochs 8 --out /kaggle/working/harvest

This is Stage 2 v0. It is not the 27M adaptation.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRAIN = ROOT / "data" / "routing" / "v1" / "train.jsonl"
DEFAULT_HELD = ROOT / "data" / "routing" / "v1" / "held_out.jsonl"

DIM = 4096
SEED = 20260826


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def feats(row: dict) -> list[int]:
    cap = row["subtask"]["capability_required"]
    tokens = [
        f"depth:{cap.get('reasoning_depth')}",
        f"tools:{cap.get('tool_use')}",
        f"stakes:{cap.get('stakes')}",
        f"ctx:{cap.get('context_pressure')}",
        f"budget:{row.get('context_signals', {}).get('remaining_budget')}",
    ]
    for domain in cap.get("domain") or []:
        tokens.append(f"dom:{domain}")
    for mid in row.get("available_models") or []:
        tokens.append(f"avail:{mid}")
    idx = []
    for tok in tokens:
        h = hash(tok) % DIM
        idx.append(h)
    return idx


def one_hot_dot(weights: list[list[float]], x: list[int], c: int) -> float:
    return sum(weights[c][i] for i in x)


def softmax(xs: list[float]) -> list[float]:
    m = max(xs)
    ex = [math.exp(v - m) for v in xs]
    z = sum(ex) or 1.0
    return [v / z for v in ex]


def train(rows: list[dict], labels: list[str], epochs: int, lr: float) -> list[list[float]]:
    k = len(labels)
    lab_i = {name: i for i, name in enumerate(labels)}
    w = [[0.0] * DIM for _ in range(k)]
    rng = random.Random(SEED)
    order = list(range(len(rows)))
    for _ in range(epochs):
        rng.shuffle(order)
        for n in order:
            row = rows[n]
            y = lab_i[row["chosen_model"]]
            x = feats(row)
            logits = [one_hot_dot(w, x, c) for c in range(k)]
            p = softmax(logits)
            for c in range(k):
                g = p[c] - (1.0 if c == y else 0.0)
                if g == 0.0:
                    continue
                step = lr * g
                for i in x:
                    w[c][i] -= step
    return w


def evaluate(rows: list[dict], labels: list[str], w: list[list[float]]) -> dict:
    correct = 0
    confs = []
    for row in rows:
        x = feats(row)
        logits = [one_hot_dot(w, x, c) for c in range(len(labels))]
        p = softmax(logits)
        pred = max(range(len(labels)), key=lambda c: p[c])
        confs.append(p[pred])
        if labels[pred] == row["chosen_model"]:
            correct += 1
    n = max(len(rows), 1)
    return {
        "n": len(rows),
        "acc": round(correct / n, 4),
        "mean_conf": round(sum(confs) / n, 4),
        "correct": correct,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--held", type=Path, default=DEFAULT_HELD)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--lr", type=float, default=0.15)
    parser.add_argument("--out", type=Path, default=ROOT / "var" / "routing-v0")
    args = parser.parse_args()

    if not args.train.is_file() or not args.held.is_file():
        print(f"missing jsonl: {args.train} / {args.held}", file=sys.stderr)
        return 2

    train_rows = load_jsonl(args.train)
    held_rows = load_jsonl(args.held)
    labels = sorted({r["chosen_model"] for r in train_rows})
    w = train(train_rows, labels, args.epochs, args.lr)
    tr = evaluate(train_rows, labels, w)
    ho = evaluate(held_rows, labels, w)

    args.out.mkdir(parents=True, exist_ok=True)
    harvest = args.out / "harvest" if args.out.name != "harvest" else args.out
    harvest.mkdir(parents=True, exist_ok=True)
    metrics = {
        "schema_version": "routing-train-v0",
        "utc": datetime.now(timezone.utc).isoformat(),
        "epochs": args.epochs,
        "lr": args.lr,
        "dim": DIM,
        "n_classes": len(labels),
        "labels": labels,
        "train": tr,
        "held_out": ho,
        "note": "hashed-tag linear head; not HRM z_H adaptation",
    }
    (harvest / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"train_acc": tr["acc"], "held_acc": ho["acc"], "n_train": tr["n"], "n_held": ho["n"]}))
    print(f"wrote {harvest / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
