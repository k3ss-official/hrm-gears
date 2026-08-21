#!/usr/bin/env python3
"""Maze + ARC-2 smokes: paper 16-step eval vs experimental Q-head early-exit.

Checkpoints: sapientinc/HRM-checkpoint-maze-30x30-hard and
sapientinc/HRM-checkpoint-ARC-2 (Wang et al., 2025). Token schemes from
the upstream dataset builders. Early-exit is *not* the paper metric.
"""

from __future__ import annotations

import gc
import sys
from dataclasses import dataclass
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hrm_gears.runtime import format_bytes, load_hrm, pick_device, run_act  # noqa: E402
from hrm_gears.tokenize import encode_arc, encode_maze, make_batch  # noqa: E402


@dataclass(frozen=True)
class TaskSpec:
    name: str
    named: Path
    fallback: Path
    seq_len: int
    encode: callable


TASKS = [
    TaskSpec(
        "maze-30x30-hard",
        ROOT / "checkpoints" / "sapientinc" / "HRM-checkpoint-maze-30x30-hard",
        ROOT / "checkpoints" / "maze-30x30-hard",
        900,
        encode_maze,
    ),
    TaskSpec(
        "ARC-2",
        ROOT / "checkpoints" / "sapientinc" / "HRM-checkpoint-ARC-2",
        ROOT / "checkpoints" / "ARC-2",
        900,
        encode_arc,
    ),
]


def resolve(task: TaskSpec) -> Path:
    for path in (task.named, task.fallback):
        if (path / "checkpoint").is_file():
            return path
    raise FileNotFoundError(f"{task.name}: run scripts/fetch_checkpoints.py")


def run_task(task: TaskSpec, preferred: torch.device) -> list[dict]:
    ckpt = resolve(task)
    print("=" * 78)
    print(f"task={task.name}")
    print(f"checkpoint_dir={ckpt}")

    device = preferred
    try:
        model, n_params = load_hrm(ckpt, task.seq_len, device)
        batch = make_batch(task.encode(), device)
        run_act(model, batch, device, dynamic=True)
    except Exception as exc:
        if preferred.type != "mps":
            raise
        print(f"MPS failed ({type(exc).__name__}: {exc}); falling back to cpu")
        device = torch.device("cpu")
        gc.collect()
        if hasattr(torch, "mps"):
            try:
                torch.mps.empty_cache()
            except Exception:
                pass
        model, n_params = load_hrm(ckpt, task.seq_len, device)
        batch = make_batch(task.encode(), device)

    print(f"device={device} params={n_params:,} halt_max_steps={model.config.halt_max_steps}")
    print(f"H_cycles={model.config.H_cycles} L_cycles={model.config.L_cycles}")

    rows = []
    for mode_name, dynamic in (("A_full16", False), ("B_early_exit", True)):
        stats = run_act(model, batch, device, dynamic=dynamic)
        stats.update(task=task.name, mode=mode_name, device=str(device), params=n_params)
        rows.append(stats)
        print(
            f"  {mode_name}: steps={stats['steps']} first_q_halt>q_cont={stats['first_qh_gt']} "
            f"logits={stats['logits_shape']} in_vocab={stats['in_vocab']} "
            f"L={stats['l_updates']} H={stats['h_updates']} "
            f"lat={stats['latency_s']:.3f}s rss={format_bytes(stats['peak_rss'])}"
        )

    speedup = rows[0]["latency_s"] / rows[1]["latency_s"] if rows[1]["latency_s"] else float("inf")
    rows[0]["speedup_vs_A"] = 1.0
    rows[1]["speedup_vs_A"] = speedup
    print(f"  speedup B vs A: {speedup:.2f}x")

    del model, batch
    gc.collect()
    if device.type == "mps":
        try:
            torch.mps.empty_cache()
        except Exception:
            pass
    return rows


def print_table(rows: list[dict]) -> None:
    headers = [
        "task", "mode", "device", "params", "logits", "valid",
        "first>", "steps", "Lupd", "Hupd", "lat_s", "speedup", "peak_rss",
    ]
    table = []
    for r in rows:
        table.append([
            r["task"],
            r["mode"],
            r["device"],
            f"{r['params']:,}",
            str(r["logits_shape"]),
            "ok" if r["in_vocab"] else "FAIL",
            str(r["first_qh_gt"]),
            str(r["steps"]),
            str(r["l_updates"]),
            str(r["h_updates"]),
            f"{r['latency_s']:.3f}",
            f"{r.get('speedup_vs_A', 1.0):.2f}x",
            format_bytes(r["peak_rss"]),
        ])
    widths = [max(len(headers[i]), max(len(row[i]) for row in table)) for i in range(len(headers))]
    print()
    print("SUMMARY")
    print(" | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("-+-".join("-" * w for w in widths))
    for row in table:
        print(" | ".join(row[i].ljust(widths[i]) for i in range(len(headers))))


def main() -> int:
    preferred = pick_device()
    print(f"preferred_device={preferred}")
    rows: list[dict] = []
    for task in TASKS:
        rows.extend(run_task(task, preferred))
    print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
