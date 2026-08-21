# Environment

## Machines

Measured on an Apple M4 Mac mini, 16 GiB unified memory, macOS, Python 3.12.11
(conda-forge), PyTorch 2.13.0 (`macosx_14_0_arm64`), MPS available.

The paper's training stack is CUDA 12.6 + FlashAttention 2/3 on NVIDIA
Ampere/Hopper (Wang et al., 2025, README). That stack **does not build here**.
We do not pretend otherwise.

## Python 3.12

Doors 1 and 2 need **Python ≥ 3.12**. `./setup` on a TTY offers to
install it (Homebrew / apt / uv) when the probe misses. `--yes` accepts
that install. Door 3 is `python:3.12-slim` and does not use the host
interpreter.

Manual recipes: [README — Python 3.12](../README.md#python-312-manual).

```bash
python3.12 --version   # ./setup also accepts this as already done
```

## Bootstrap

Door 1 (preferred):

```bash
./setup
```

Door 2 (unwrapped):

```bash
./scripts/bootstrap_env.sh
source .venv/bin/activate
python scripts/fetch_checkpoints.py   # Hugging Face; weights are not in git
```

Door 3 (CPU container; does not touch the host `.venv`):

```bash
docker compose run --rm setup
```

`bootstrap_env.sh` writes a `.pth` into site-packages so

```python
from flash_attn import flash_attn_func
```

resolves to `hrm_gears/compat/flash_attn`. Upstream `models/layers.py` is
unmodified.

## What is installed vs what is not

| Piece | Status |
| --- | --- |
| `requirements.txt` (torch, hydra, wandb, huggingface_hub, adam-atan2, …) | installed |
| `numpy` (used by dataset code, omitted upstream) | installed |
| FlashAttention 2/3 CUDA extensions | **not** installed |
| CUDA toolkit | **not** installed |
| Published checkpoints | downloaded locally, gitignored |

## Device policy

`hrm_gears.runtime.pick_device()` prefers CUDA, then MPS, then CPU. Smoke harnesses
attempt MPS, catch SDPA/device failures, and retry on CPU. `empty_carry`
allocates on CPU; `move_carry` places `z_H` / `z_L` on the compute device.

`torch.compile` is left off (`DISABLE_COMPILE` is implicit). Compiled graphs
are how the Hugging Face keys acquire the `_orig_mod.` prefix; we strip that
on load rather than compiling locally.

## Disk

| Path | Role | In git |
| --- | --- | --- |
| `.venv/` | interpreter | no |
| `checkpoints/sudoku-extreme/` | ~104 MiB | no |
| `checkpoints/maze-30x30-hard/` | ~104 MiB | no |
| `checkpoints/ARC-2/` | ~2.1 GiB | no |
| `checkpoints/sapientinc/*` | stable name symlinks | no |

## Reproducing the smoke numbers

```bash
source .venv/bin/activate
python scripts/smoke_test_inference.py
python scripts/smoke_test_all.py
```

See [experiments.md](experiments.md).

The M4 stops here. Adaptation uses Twin-T4 harvest on **Kaggle**
**GPU T4 x2** (2 × NVIDIA Tesla T4): pack → spin → run → harvest →
kill. ~30 GPU hours/week, phone-verified, no leftover VM. See
[compute.md](compute.md).
