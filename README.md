# hrm-gears

**Adapt Sapient's 27M Hierarchical Reasoning Model into a local, cheapest-viable model router.**

This is not a Transformer project. HRM (Wang et al., 2025) is a dual-timescale
recurrent network with an ACT halt head. We are measuring whether that
architecture can sit in front of a tool-using agent harness and pick the
lowest-cost model that can still do the subtask.

The first consumer is **Hermes** (Nous Research). The interface is a
capability matrix plus a discrete choice — any harness that can annotate a
subtask and honour a model id can point at the same unit. Hermes is the
design centre, not a hard dependency.

Pre-work was not "stay on Transformers because they are easy". Survey
included Inception **Mercury 2** (diffusion LM), **Sakana AI**
([sakana.ai](https://sakana.ai/) — Fugu / Namazu API), and TRM. HRM is the
line known longest: dual timescale plus an ACT halt head already looks like
a monitor that *allots* work. Routing is allocation under trained
parameters, not an essay. See [`docs/architecture.md`](docs/architecture.md#pre-work).

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

Repo: [`k3ss-official/hrm-gears`](https://github.com/k3ss-official/hrm-gears).
The Python package import is still `hrm_gear`.

## Install — three doors

### Door 1 — `./setup` (default)

Single entrypoint. Probes Python / platform / MPS-or-CUDA / disk, creates or
reuses `.venv`, installs, fetches the three official checkpoints, runs Sudoku
then Maze+ARC-2 smokes. Narrated stages. Non-zero exit on fail.

```bash
git clone https://github.com/k3ss-official/hrm-gears.git
cd hrm-gears
./setup
```

### Door 2 — techie manual

Same steps, unwrapped. Use this when you already have a venv or you are
debugging one stage.

```bash
./scripts/bootstrap_env.sh
source .venv/bin/activate
python scripts/fetch_checkpoints.py
python scripts/smoke_test_inference.py          # Sudoku ACT
python scripts/smoke_test_all.py                # Maze + ARC-2, A vs B
```

CUDA + FlashAttention reproduction of the *paper* follows the upstream
README at [`docs/upstream/HRM.README.md`](docs/upstream/HRM.README.md).
Do not mix those numbers with SDPA/MPS runs.

### Door 3 — Docker one-shot

Same `./setup`, inside a container (CPU). The image is the install door,
not the Twin-T4 harvest pack (`docs/compute.md`).

```bash
docker compose run --rm setup
```

If `Dockerfile` / `compose.yaml` are not in this tree yet, use Door 1.
GPU pack/harvest is a separate path.

## MVP vs Stage 2

| | **MVP (this tree, now)** | **Stage 2 (not this PR)** |
| --- | --- | --- |
| What ships | Load published 27M weights on M4. `./setup`. Frozen vendor matrix. Sudoku + Maze + ARC-2 smokes. | Routing classification head. Experience flywheel. Twin-T4 harvest training. Daily model-intel scrape. |
| Matrix | Hard-coded snapshot. Manual refresh. | Re-rank from live catalogs; infrequent retrain. |
| Training | **Not started. Do not implement.** | Supervised bootstrap on synthetic + Hermes traces, then continual log→update with a held-out suite. |
| Daily scrape | **Out of scope.** | Lightweight freshness, then closed loop. |

The published puzzle weights do **not** route LLMs. They prove the
architecture can do hierarchical discrete search from little data.
Adaptation is Stage 2.

The M4 is the smoke bench. Training uses **Twin-T4 harvest** on Kaggle
**GPU T4 x2** — pack / spin / run / harvest / kill. See
[`docs/compute.md`](docs/compute.md).

## MVP vendor / model table

Locked sources only. Strict order: **free → non-frontier subscription →
frontier subscription → non-frontier API → frontier API**. Within a tier,
cheaper / faster wins. Machine-readable copy:
[`config/model_matrix.v1.yaml`](config/model_matrix.v1.yaml).

Vendors: **OpenCode Go**, **Nous Portal**, **OpenAI OAuth**, **OpenCode Zen**,
**Nvidia**, **OpenRouter**. Nothing else in MVP.

| Tier | ID | Source | Notes |
| --- | --- | --- | --- |
| 1 Free | `free-opencode-zen` | OpenCode Zen | Primary free lane |
| 1 Free | `free-openrouter` | OpenRouter | Rotating $0 pool |
| 1 Free | `free-nous` | Nous Portal | Temporary free windows |
| 2 Non-frontier sub | `nous-deepseek` | Nous Portal | Cheap reasoning |
| 2 Non-frontier sub | `nous-nemotron` | Nous Portal | Coding / general |
| 2 Non-frontier sub | `nous-qwen` | Nous Portal | Qwen3-class |
| 2 Non-frontier sub | `nous-hy3` | Nous Portal | Mid fill |
| 2 Non-frontier sub | `openai-nonfrontier` | OpenAI OAuth | Mini / non-Sol class |
| 3 Frontier sub | `openai-gpt56-sol` | OpenAI OAuth | High-end reasoning |
| 3 Frontier sub | `nous-fable5` | Nous Portal | Agentic |
| 3 Frontier sub | `nous-gemini` | Nous Portal | Long context / multimodal |
| 3 Frontier sub | `opencode-go-frontier` | OpenCode Go | Frontier exposed via Go |
| 4 Non-frontier API | `openrouter-mid` | OpenRouter | Cost-controlled |
| 4 Non-frontier API | `nvidia-nemotron` | Nvidia | Nemotron API |
| 4 Non-frontier API | `opencode-zen-paid` | OpenCode Zen | Paid non-frontier on Zen |
| 5 Frontier API | `openrouter-frontier` | OpenRouter | Last resort |
| 5 Frontier API | `nvidia-frontier` | Nvidia | Last resort |

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
| `./setup` entrypoint | **this change** |
| Routing head / traces / Twin-T4 harvest | **Stage 2 — not started** |

Numbers: [`docs/experiments.md`](docs/experiments.md).
Burst-GPU plan: [`docs/compute.md`](docs/compute.md).

## Architecture in one page

`z_H` plans slowly. `z_L` refines quickly. One ACT step runs
`H_cycles × L_cycles` inner L-updates and `H_cycles` H-updates, then a
two-logit Q-head (`q_halt`, `q_continue`). Paper eval always takes
`halt_max_steps = 16`. Training may stop early.

Full reading: [`docs/architecture.md`](docs/architecture.md).

## Layout

```
./setup                   Door 1 — probe, venv, fetch, smokes
hrm_gear/                 runtime (load, ACT, token schemes, SDPA shim)
scripts/                  bootstrap, checkpoint fetch, smokes, setup
config/model_matrix.v1.yaml
docs/                     architecture, environment, experiments, routing, compute
models/  pretrain.py …    unmodified upstream HRM (Wang et al., 2025)
```

## License

Apache License 2.0. Upstream HRM is Apache-2.0; so are our additions.
See `LICENSE` and `NOTICE`. Checkpoints are fetched from Hugging Face and
are **not** stored in git.

## Thanks

Nous Research, and [@Teknium](https://x.com/Teknium1) in particular —
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
