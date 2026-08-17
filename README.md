# hrm-gear

**Adapt Sapient's 27M Hierarchical Reasoning Model into a local, cheapest-viable model router.**

This is not a Transformer project. HRM (Wang et al., 2025) is a dual-timescale
recurrent network with an ACT halt head. We are measuring whether that
architecture can sit inside a Hermes-style orchestrator and pick the lowest-cost
model that can still do the subtask.

The original research code, paper, and checkpoints are **Sapient Intelligence's**.
They are cited in [`NOTICE`](NOTICE) and [`docs/REFERENCES.md`](docs/REFERENCES.md).
This repository is an Apache-2.0 derivative: their tree, plus a documented
Apple-Silicon runtime, inference harnesses, and a routing contract.

```
rider  = Hermes orchestrator
bike   = the agent harness
gears  = vendor models (free → frontier API)
derailleur = HRM (candidate)
```

## Status

| Item | State |
| --- | --- |
| Fresh clone of `sapientinc/HRM` | done |
| MPS env + SDPA FlashAttention stand-in | done |
| Strict load of Sudoku / Maze / ARC-2 weights | done |
| ACT smoke tests (16-step vs experimental early-exit) | done |
| Routing head / training data / Kaggle run | **not started** |

Measured, not hoped: see [`docs/experiments.md`](docs/experiments.md).

## Architecture in one page

`z_H` plans slowly. `z_L` refines quickly. One ACT step runs
`H_cycles × L_cycles` inner L-updates and `H_cycles` H-updates, then a
two-logit Q-head (`q_halt`, `q_continue`). Paper eval always takes
`halt_max_steps = 16`. Training may stop early.

Full reading: [`docs/architecture.md`](docs/architecture.md).

## Quick start (M4 / no NVIDIA)

```bash
git clone https://github.com/k3ss-official/hrm-gear.git
cd hrm-gear
./scripts/bootstrap_env.sh
source .venv/bin/activate
python scripts/fetch_checkpoints.py
python scripts/smoke_test_inference.py          # Sudoku ACT
python scripts/smoke_test_all.py                # Maze + ARC-2, A vs B
```

CUDA + FlashAttention reproduction of the *paper* follows the upstream
README at [`docs/upstream/HRM.README.md`](docs/upstream/HRM.README.md).
Do not mix those numbers with SDPA/MPS runs.

## Layout

```
hrm_gear/                 our runtime (load, ACT, token schemes, SDPA shim)
scripts/                  bootstrap, checkpoint fetch, smokes
config/model_matrix.v1.yaml
docs/                     architecture, environment, experiments, routing
models/  pretrain.py …    unmodified upstream HRM (Wang et al., 2025)
```

## License

Apache License 2.0. Upstream HRM is Apache-2.0; so are our additions.
See `LICENSE` and `NOTICE`. Checkpoints are fetched from Hugging Face and
are **not** stored in git.

## Thanks

Sapient Intelligence — for publishing a 27M hierarchical reasoner instead
of another 7B Transformer. Graves (2016) for ACT. Chollet / ARC Prize /
ConceptARC for the puzzle distributions the original model was trained on.
Dao et al. for FlashAttention, which this fork deliberately *does not*
require at inference time.

Full list: [`docs/REFERENCES.md`](docs/REFERENCES.md).
