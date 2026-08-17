# hrm-gears

**Adapt Sapient's 27M Hierarchical Reasoning Model into a local, cheapest-viable model router.**

This is not a Transformer project. HRM (Wang et al., 2025) is a dual-timescale
recurrent network with an ACT halt head. We are measuring whether that
architecture can sit in front of a tool-using agent harness and pick the
lowest-cost model that can still do the subtask.

The first consumer is **Hermes** ([@NousResearch](https://x.com/NousResearch)). The interface is a
capability matrix plus a discrete choice — any harness that can annotate a
subtask and honour a model id can point at the same unit. Hermes is the
design centre, not a hard dependency.

Pre-work was not "stay on Transformers because they are easy". Survey
included Inception **Mercury 2** (diffusion LM), **Sakana AI**
([sakana.ai](https://sakana.ai/) — Fugu / Namazu API), and TRM. HRM is the line known longest: dual timescale plus
an ACT halt head already looks like a monitor that *allots* work.
Routing is allocation under trained parameters, not an essay. See
[`docs/architecture.md`](docs/architecture.md#pre-work).

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

Local cursory tests of the published weights, M4 / MPS / SDPA shim.
Not paper-task leaderboards. Load + ACT forward + in-vocab outputs.

| Item | State |
| --- | --- |
| Fresh clone of `sapientinc/HRM` | done |
| MPS env + SDPA FlashAttention stand-in | done |
| Strict load — Sudoku / Maze / ARC-2 | **PASS** |
| ACT smoke, 16-step (Sudoku) | **PASS** (Q-head would halt at step 2) |
| ACT smoke, Maze + ARC-2, 16-step vs early-exit | **PASS** (Q-head did not cross on constructed boards) |
| Routing head / traces / Twin-T4 harvest | **not started** |

Numbers: [`docs/experiments.md`](docs/experiments.md).
Burst-GPU plan: [`docs/compute.md`](docs/compute.md).

## Architecture in one page

`z_H` plans slowly. `z_L` refines quickly. One ACT step runs
`H_cycles × L_cycles` inner L-updates and `H_cycles` H-updates, then a
two-logit Q-head (`q_halt`, `q_continue`). Paper eval always takes
`halt_max_steps = 16`. Training may stop early.

Full reading: [`docs/architecture.md`](docs/architecture.md).

## Quick start (M4 / no NVIDIA)

```bash
git clone https://github.com/k3ss-official/hrm-gears.git
cd hrm-gears
./scripts/bootstrap_env.sh
source .venv/bin/activate
python scripts/fetch_checkpoints.py
python scripts/smoke_test_inference.py          # Sudoku ACT
python scripts/smoke_test_all.py                # Maze + ARC-2, A vs B
```

CUDA + FlashAttention reproduction of the *paper* follows the upstream
README at [`docs/upstream/HRM.README.md`](docs/upstream/HRM.README.md).
Do not mix those numbers with SDPA/MPS runs.

Adaptation does **not** stay on the M4. The M4 is the smoke bench. Training
uses **Twin-T4 harvest**: pack the run, spin a Kaggle **GPU T4 x2** session
(2 × NVIDIA Tesla T4), train, pull artifacts, kill the VM. Weekly free
quota is on the order of 30 GPU hours — a burst, not a lease. Details in
[`docs/compute.md`](docs/compute.md).

## Layout

```
hrm_gear/                 our runtime (load, ACT, token schemes, SDPA shim)
scripts/                  bootstrap, checkpoint fetch, smokes
config/model_matrix.v1.yaml
docs/                     architecture, environment, experiments, routing, compute
models/  pretrain.py …    unmodified upstream HRM (Wang et al., 2025)
```

## License

Apache License 2.0. Upstream HRM is Apache-2.0; so are our additions.
See `LICENSE` and `NOTICE`. Checkpoints are fetched from Hugging Face and
are **not** stored in git.

## Thanks

[@NousResearch](https://x.com/NousResearch), and [@Teknium](https://x.com/Teknium1) in particular —
Hermes is why this router exists. The first install target is a Hermes
harness; the contract is harness-agnostic on purpose.

[@tonysimmons_](https://x.com/tonysimmons_) — for getting this off the
whiteboard and onto a disk.

Sapient Intelligence — for publishing a 27M hierarchical reasoner instead
of another 7B Transformer. Graves (2016) for ACT. Chollet / ARC Prize /
ConceptARC for the puzzle distributions the original model was trained on.
Dao et al. for FlashAttention, which this fork deliberately *does not*
require at inference time.

Full list: [`docs/REFERENCES.md`](docs/REFERENCES.md).
