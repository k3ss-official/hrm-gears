#!/usr/bin/env python3
"""Sudoku ACT smoke test against the published Sapient checkpoint.

Loads HierarchicalReasoningModel_ACTV1 with a strict state_dict, runs the
eval ACT loop (16 steps) on a format-correct 9x9 encoding, and prints
logit shapes, the Q-head trajectory, recurrence counts, latency, and RSS.

Weights: sapientinc/HRM-checkpoint-sudoku-extreme (Wang et al., 2025).
Token scheme: dataset/build_sudoku_dataset.py (cell + 1, PAD = 0).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hrm_gears.runtime import (  # noqa: E402
    format_bytes,
    load_hrm,
    pick_device,
    run_act,
)
from hrm_gears.tokenize import decode_sudoku, encode_sudoku, make_batch  # noqa: E402

DEFAULT = ROOT / "checkpoints" / "sapientinc" / "HRM-checkpoint-sudoku-extreme"
FALLBACK = ROOT / "checkpoints" / "sudoku-extreme"


def resolve_dir(explicit: Path) -> Path:
    for path in (explicit, DEFAULT, FALLBACK):
        if (path / "checkpoint").is_file():
            return path
    raise FileNotFoundError("Sudoku checkpoint not found. Run scripts/fetch_checkpoints.py")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ckpt-dir", type=Path, default=DEFAULT)
    args = parser.parse_args()
    ckpt = resolve_dir(args.ckpt_dir)
    preferred = pick_device()
    print(f"checkpoint_dir: {ckpt}")
    print(f"preferred_device: {preferred}")

    device = preferred
    try:
        model, n_params = load_hrm(ckpt, seq_len=81, device=device)
        batch = make_batch(encode_sudoku(), device)
        stats = run_act(model, batch, device, dynamic=False)
    except Exception as exc:
        if preferred.type != "mps":
            raise
        print(f"MPS forward failed ({type(exc).__name__}: {exc})")
        print("falling back to cpu")
        device = torch.device("cpu")
        model, n_params = load_hrm(ckpt, seq_len=81, device=device)
        batch = make_batch(encode_sudoku(), device)
        stats = run_act(model, batch, device, dynamic=False)

    pred = stats["pred"]
    pred_grid = decode_sudoku(pred[0])
    input_grid = decode_sudoku(batch["inputs"][0])

    print(f"device_used: {device}")
    print(f"params: {n_params:,}")
    print(f"dtype: {model.config.forward_dtype}")
    print(
        f"H_cycles={stats['h_cycles']} L_cycles={stats['l_cycles']} "
        f"halt_max_steps={model.config.halt_max_steps}"
    )
    print(f"inputs.shape: {tuple(batch['inputs'].shape)}  tokens [PAD=0, blank=1, digits=2..10]")
    print("input_grid (decoded 0-9, 0=blank):")
    for row in input_grid:
        print(" ", " ".join(str(v) if v else "." for v in row))
    print(f"logits.shape: {stats['logits_shape']}")
    print("predicted_grid (decoded 0-9):")
    for row in pred_grid:
        print(" ", " ".join(str(v) if v else "." for v in row))
    print("act_step_log:")
    for rec in stats["step_log"]:
        print(
            f"  step={rec['step']:2d} halted={int(rec['halted'])} "
            f"would_halt={int(rec['would_halt'])} "
            f"q_halt={rec['q_halt']:+.4f} q_continue={rec['q_continue']:+.4f}"
        )
    print(f"act_steps_executed: {stats['steps']}")
    print("eval_halt_policy: max_steps (training-only early halt disabled)")
    print(f"first_q_halt_gt_q_continue_step: {stats['first_qh_gt']}")
    print(f"total_L_level_updates: {stats['l_updates']}")
    print(f"total_H_level_updates: {stats['h_updates']}")
    print(f"forward_latency_s: {stats['latency_s']:.4f}")
    print(f"peak_rss: {format_bytes(stats['peak_rss'])} ({stats['peak_rss']} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
