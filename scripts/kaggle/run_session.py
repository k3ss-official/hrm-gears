#!/usr/bin/env python3
"""On-box Twin-T4 session body: CUDA inventory, Sudoku ACT smoke, harvest dir.

Runs on a Kaggle GPU T4 x2 notebook (or any CUDA box). Writes
<out>/harvest/{MANIFEST.json,smoke.json,session.log}.

Refuses routing-head / Stage 2 training. First harvest is plumbing + a
published-weight smoke so we know the pair of T4s actually works.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Kaggle's image rarely has FlashAttention CUDA extensions. Use the SDPA shim.
COMPAT = ROOT / "hrm_gear" / "compat"
if str(COMPAT) not in sys.path:
    sys.path.insert(0, str(COMPAT))


def nvidia_smi() -> str:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version", "--format=csv,noheader"],
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"nvidia-smi failed: {exc}"


def load_pack_manifest() -> dict:
    candidates = [
        ROOT / "PACK_MANIFEST.json",
        Path("/kaggle/working/PACK_MANIFEST.json"),
    ]
    input_root = Path("/kaggle/input")
    if input_root.is_dir():
        candidates.extend(input_root.glob("*/MANIFEST.json"))
    for candidate in candidates:
        if candidate.is_file():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return {}


def resolve_sudoku() -> Path:
    from huggingface_hub import snapshot_download

    named = ROOT / "checkpoints" / "sapientinc" / "HRM-checkpoint-sudoku-extreme"
    local = ROOT / "checkpoints" / "sudoku-extreme"
    for path in (named, local):
        if (path / "checkpoint").is_file():
            return path
    local.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id="sapientinc/HRM-checkpoint-sudoku-extreme",
        local_dir=str(local),
    )
    named.parent.mkdir(parents=True, exist_ok=True)
    if not named.exists():
        try:
            named.symlink_to(Path("..") / "sudoku-extreme")
        except OSError:
            pass
    return local


def run_smoke(device_name: str) -> dict:
    import torch

    from hrm_gear.runtime import load_hrm, run_act
    from hrm_gear.tokenize import decode_sudoku, encode_sudoku, make_batch

    device = torch.device(device_name)
    ckpt = resolve_sudoku()
    model, n_params = load_hrm(ckpt, seq_len=81, device=device)
    batch = make_batch(encode_sudoku(), device)
    stats = run_act(model, batch, device, dynamic=False)
    pred_grid = decode_sudoku(stats["pred"][0])
    return {
        "checkpoint_dir": str(ckpt),
        "device": str(device),
        "params": n_params,
        "logits_shape": list(stats["logits_shape"]),
        "steps": stats["steps"],
        "first_q_halt_gt_q_continue_step": stats["first_qh_gt"],
        "l_updates": stats["l_updates"],
        "h_updates": stats["h_updates"],
        "latency_s": stats["latency_s"],
        "peak_rss": stats["peak_rss"],
        "predicted_grid": pred_grid,
        "givens_preserved": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(os.environ.get("HARVEST_OUT", "/kaggle/working")),
        help="Directory that will contain harvest/ (default: /kaggle/working)",
    )
    parser.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Permit a local dry-run without CUDA. Not a Twin-T4 harvest.",
    )
    parser.add_argument(
        "--train-routing",
        action="store_true",
        help="Rejected. Stage 2 is out of scope for this path.",
    )
    args = parser.parse_args()

    if args.train_routing or os.environ.get("TRAIN_ROUTING") == "1":
        print("BLOCKED: Stage 2 routing training is not this path.", file=sys.stderr)
        return 3

    import torch

    smi = nvidia_smi()
    cuda = torch.cuda.is_available()
    n_gpu = torch.cuda.device_count() if cuda else 0
    if cuda:
        device_name = "cuda"
    elif args.allow_cpu:
        from hrm_gear.runtime import pick_device

        device_name = str(pick_device())
    else:
        print("Twin-T4 harvest requires CUDA. This box has none.", file=sys.stderr)
        print(smi, file=sys.stderr)
        return 1

    on_kaggle = Path("/kaggle/working").is_dir()
    pack = load_pack_manifest()
    smoke = run_smoke(device_name)

    harvest = args.out / "harvest"
    harvest.mkdir(parents=True, exist_ok=True)
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "schema_version": "1",
        "purpose": "twin-t4-harvest",
        "stage": "smoke",
        "stage2_routing_training": False,
        "packed": pack,
        "harvested_utc": utc,
        "on_kaggle": on_kaggle,
        "cuda": cuda,
        "device_count": n_gpu,
        "device_used": device_name,
        "allow_cpu": args.allow_cpu,
        "nvidia_smi": smi,
        "torch": torch.__version__,
        "expect_accelerator": "GPU T4 x2 (2 x NVIDIA Tesla T4)",
        "t4_x2_seen": n_gpu == 2 and "T4" in smi,
    }
    (harvest / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (harvest / "smoke.json").write_text(
        json.dumps(smoke, indent=2) + "\n", encoding="utf-8"
    )
    log = (
        f"harvested_utc={utc}\n"
        f"cuda={cuda} device_count={n_gpu} device_used={device_name}\n"
        f"nvidia_smi:\n{smi}\n"
        f"params={smoke['params']} first_halt={smoke['first_q_halt_gt_q_continue_step']}\n"
        f"latency_s={smoke['latency_s']:.4f}\n"
        "stage2_routing_training=false\n"
    )
    (harvest / "session.log").write_text(log, encoding="utf-8")
    print(log, end="")
    print(f"harvest: {harvest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
