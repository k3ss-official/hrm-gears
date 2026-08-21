"""Shared load/device/ACT helpers for published HRM checkpoints.

Upstream `evaluate.py` assumes CUDA, NCCL, `torch.compile`, and
`map_location="cuda"`. Those assumptions are correct for the paper's
8-GPU training setup and wrong on an M4. This module is the thinnest
adapter that still does a *strict* `load_state_dict` of the released
weights.

Checkpoint keys from Hugging Face are compiled (`_orig_mod.`) and
wrapped in `ACTLossHead` (`model.`). After stripping those two prefixes
the remaining tree matches `HierarchicalReasoningModel_ACTV1`.
"""

from __future__ import annotations

import resource
import sys
import time
from pathlib import Path
from typing import Any

import torch
import yaml

from models.hrm.hrm_act_v1 import HierarchicalReasoningModel_ACTV1


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def rss_bytes() -> int:
    """Peak RSS. macOS reports bytes; Linux reports kilobytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(usage) if sys.platform == "darwin" else int(usage) * 1024


def format_bytes(n: int) -> str:
    return f"{n / (1024 ** 2):.1f} MiB"


def strip_state_dict(state: dict) -> dict:
    out = {}
    for key, value in state.items():
        key = key.removeprefix("_orig_mod.")
        key = key.removeprefix("model.")
        out[key] = value
    return out


def load_arch(ckpt_dir: Path) -> dict:
    with (ckpt_dir / "all_config.yaml").open() as handle:
        return yaml.safe_load(handle)["arch"]


def load_hrm(ckpt_dir: Path, seq_len: int, device: torch.device) -> tuple[HierarchicalReasoningModel_ACTV1, int]:
    """Instantiate ACT-HRM and strictly load a published checkpoint."""
    arch = load_arch(ckpt_dir)
    raw = torch.load(ckpt_dir / "checkpoint", map_location="cpu", weights_only=False)
    state = strip_state_dict(raw)
    vocab = int(state["inner.embed_tokens.embedding_weight"].shape[0])
    n_puzzle = int(state["inner.puzzle_emb.weights"].shape[0])
    cfg = {
        **{k: v for k, v in arch.items() if k not in {"name", "loss"}},
        "batch_size": 1,
        "vocab_size": vocab,
        "seq_len": seq_len,
        "num_puzzle_identifiers": n_puzzle,
        "causal": False,
    }
    model = HierarchicalReasoningModel_ACTV1(cfg)
    model.load_state_dict(state, strict=True)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    del raw, state
    return model.to(device), n_params


def move_carry(carry: Any, device: torch.device) -> Any:
    """`empty_carry` allocates on CPU. Move the recurrent state to `device`."""
    carry.inner_carry.z_H = carry.inner_carry.z_H.to(device)
    carry.inner_carry.z_L = carry.inner_carry.z_L.to(device)
    carry.steps = carry.steps.to(device)
    carry.halted = carry.halted.to(device)
    carry.current_data = {key: value.to(device) for key, value in carry.current_data.items()}
    return carry


def run_act(
    model: HierarchicalReasoningModel_ACTV1,
    batch: dict[str, torch.Tensor],
    device: torch.device,
    *,
    dynamic: bool = False,
) -> dict[str, Any]:
    """One ACT rollout.

    Mode A (`dynamic=False`): honour eval policy — run to `halt_max_steps`.
    Mode B (`dynamic=True`): stop on the first `q_halt > q_continue`.

    Upstream eval *never* early-stops; the Q-head comparison is training-only
    (`hrm_act_v1.py`). Mode B is an experimental inference policy, not a
    reproduction of the paper's reported numbers.
    """
    carry = move_carry(model.initial_carry(batch), device)
    h_cycles = int(model.config.H_cycles)
    l_cycles = int(model.config.L_cycles)
    first_qh_gt: int | None = None
    last_outputs = None
    steps_run = 0
    step_log: list[dict[str, Any]] = []

    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(int(model.config.halt_max_steps)):
            carry, outputs = model(carry=carry, batch=batch)
            last_outputs = outputs
            steps_run += 1
            q_halt = outputs["q_halt_logits"]
            q_cont = outputs["q_continue_logits"]
            would_halt = bool((q_halt > q_cont)[0].item())
            if would_halt and first_qh_gt is None:
                first_qh_gt = steps_run
            step_log.append(
                {
                    "step": steps_run,
                    "halted": bool(carry.halted[0].item()),
                    "would_halt": would_halt,
                    "q_halt": float(q_halt[0].item()),
                    "q_continue": float(q_cont[0].item()),
                }
            )
            if dynamic and would_halt:
                break
            if bool(carry.halted.all().item()):
                break
        if device.type == "mps":
            torch.mps.synchronize()
    latency_s = time.perf_counter() - t0

    assert last_outputs is not None
    logits = last_outputs["logits"]
    pred = logits.argmax(dim=-1)
    vocab = logits.shape[-1]
    return {
        "carry": carry,
        "outputs": last_outputs,
        "pred": pred,
        "steps": steps_run,
        "first_qh_gt": first_qh_gt,
        "latency_s": latency_s,
        "logits_shape": tuple(logits.shape),
        "pred_shape": tuple(pred.shape),
        "in_vocab": bool(((pred >= 0) & (pred < vocab)).all().item()),
        "l_updates": steps_run * h_cycles * l_cycles,
        "h_updates": steps_run * h_cycles,
        "step_log": step_log,
        "peak_rss": rss_bytes(),
        "h_cycles": h_cycles,
        "l_cycles": l_cycles,
    }
