# Compute — Twin-T4 harvest on Kaggle

The M4 Mac mini is the smoke bench. It has no NVIDIA GPU. Sixteen
gigabytes of unified memory will load the 27M trunk; it will not be the
adaptation box, and we will not rent a GPU to sit idle.

Training and any CUDA number that we intend to cite go through
**Kaggle Notebooks**, product name **GPU T4 x2**. Thanks to Kaggle for
that free dual-T4 product — this repo is built around using it as a
burst, not a lease.

Cite: [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks),
[T4 x2 announcement](https://www.kaggle.com/product-feedback/361104),
[29 GB / 4 CPU GPU-notebook update](https://www.kaggle.com/product-feedback/448251),
[30 GPU hours / week](https://www.kaggle.com/general/108481),
[Kaggle API](https://github.com/Kaggle/kaggle-api).

## Hardware and limits (as shipped)

| | |
| --- | --- |
| Product | Kaggle Notebooks, accelerator **GPU T4 x2** |
| Cards | **2 × NVIDIA Tesla T4**, 16 GB VRAM each (~32 GB combined) |
| Host RAM | **29 GB** on current GPU notebooks |
| CPUs | **4** on GPU notebooks |
| Weekly GPU quota | **~30 GPU hours / week**, phone-verified, no credit card |
| Session cap | **12 hours** execution on GPU/CPU sessions (TPU is 9 hours) |
| Idle | an *interactive* editor session dies if left idle (~20 min historically). **Save Version → Save & Run All** keeps running until the 12 h cap. |
| Persistence | none. The VM is gone when the session stops. Only committed **Output** and Datasets survive. |
| Extra hours | optional Colab Pro / Pro+ link adds 15 / 30 GPU hours. Not required. |

Quota is weekly and finite. Hover **Quota: X / 30 hrs** on the notebook.
Leave a T4 x2 session running and you burn the week on idle CUDA
context. This is a burst you borrow and give back, not a machine you own.

Phone verification is a one-time Kaggle Settings step. GPU / TPU stay
locked until that OTP lands. No card is required for the free 30 hours.

`enable_gpu: true` in `kernel-metadata.json` is **not** enough to
guarantee T4 x2 vs P100. Always set **Session → Accelerator → GPU T4 x2**
in the Kaggle UI and confirm `nvidia-smi` shows two T4s.

## What Twin-T4 harvest is

1. **Pack** — a replayable bundle: git SHA, slim tree, notebook, manifest.
   Weights stay off the pack by default; the session fetches them.
2. **Spin** — open a Kaggle notebook only when a run is queued.
   Accelerator **GPU T4 x2**, Internet **On**.
3. **Run** — inventory the cards, smoke, then (later) train. Checkpoint
   into `/kaggle/working/harvest/` because the session *will* die.
4. **Harvest** — pull Output off the box with the Kaggle API. Durable
   object is the artifact + the SHA that produced it.
5. **Kill** — Stop session. Confirm nothing is running. Next week, pack
   again from the harvested artifact, not from folklore.

The first committed harvest is **CUDA plumbing + the published Sudoku
ACT smoke**. It is not Stage 2 routing-head training. Do not pass
`--train-routing`.

## 9 steps

Account is already phone-verified. No card.

1. On the M4, from the repo root:

   ```bash
   python scripts/kaggle/pack.py
   ```

   Note `run_id`, `git_sha`, and `pack: var/kaggle-pack/<run_id>/`.

2. [kaggle.com](https://www.kaggle.com) → **Create** → **New Notebook**.

3. **Session options**: Accelerator **GPU T4 x2**. Internet **On**.
   Confirm Quota is not `30 / 30 hrs`.

4. **File → Import Notebook** → `scripts/kaggle/twin_t4.ipynb`
   (or the copy under the pack dir). Keep the notebook **private**.

5. Optional pin: add a session env var `HRM_GEARS_SHA=<sha from step 1>`
   so the clone checks out that commit. Otherwise it tracks `main`.

6. **Save Version → Save & Run All (Commit)**. Do not babysit an
   interactive editor for a multi-hour run — commit it.

7. When the version is complete, Output must contain
   `harvest/MANIFEST.json`, `harvest/smoke.json`, `harvest/session.log`.
   `t4_x2_seen` should be `true`. If `device_count` is 1, you got P100;
   discard and re-run on T4 x2.

8. Pull the artifacts (API token from
   [Kaggle Settings](https://www.kaggle.com/settings), never committed):

   ```bash
   pip install kaggle   # once
   python scripts/kaggle/harvest.py --kernel "$KAGGLE_USERNAME/hrm-gears-twin-t4"
   ```

9. **Stop** the session. Account → **Code** → nothing running. The VM
   is gone. Keep `var/kaggle-harvest/…` on the Hermes volume.

That is the whole path. There is no leftover instance to ssh into.

## What the pack contains

`scripts/kaggle/pack.py` writes `var/kaggle-pack/<utc>-<sha7>/`:

| Path | Role |
| --- | --- |
| `MANIFEST.json` | run id, git SHA, dirty flag, stage=`smoke` |
| `tree/` | slim source (no `.venv`, no `dataset/raw-data`, no ARC weights) |
| `twin_t4.ipynb` | session notebook |
| `kernel-metadata.json` | Kaggle API stub (`enable_gpu`, internet on) |

`--include-sudoku-ckpt` copies the ~104 MiB Sudoku weights. Default is
to let the session `snapshot_download` them. Do not pack ARC-2 (~2.1 GiB)
through a dataset upload for a smoke.

`var/` is gitignored.

## What already ran locally (PASS)

Cursory inference on the M4, PyTorch 2.13.0 MPS, SDPA stand-in. Not
paper-task test-set scores. Strict `load_state_dict`, ACT loop, in-vocab
outputs. Details in [experiments.md](experiments.md).

| Check | Result |
| --- | --- |
| Sudoku-extreme weights, 16-step ACT | **PASS** |
| Maze-30x30-hard weights, 16-step vs early-exit | **PASS** (Q-head never crossed on the constructed board) |
| ARC-2 weights, 16-step vs early-exit | **PASS** (same; RSS ~3 GiB from the puzzle-ID table) |

No Twin-T4 harvest has been pulled yet. The next number that matters is
a `harvest/MANIFEST.json` with `t4_x2_seen: true`.

**BLOCKED on this M4:** `~/.kaggle/kaggle.json` is not present, so
`scripts/kaggle/harvest.py` cannot pull Output. Pack + notebook import
still work. Do not invent a live harvest without the API token.

## What this path will not do

- Stage 2 routing-head training, synthetic route dumps, or Hermes
  flywheel updates. `run_session.py --train-routing` exits 3.
- Keep a GPU warm between runs.
- Treat Colab as primary (overflow only; quota is less predictable).
- Use Oracle Always Free (ARM/CPU, out).
- Fight the M4 install path. Bring-up is Door 1 `./setup` (Door 2 is
  the unwrapped `./scripts/bootstrap_env.sh`). The optional CUDA Docker
  skeleton is `scripts/kaggle/Dockerfile` and is **not** Door 3
  (`docker compose run --rm setup`).

## Optional CUDA Docker (not Kaggle, not M4)

If you already have a local NVIDIA box and want the same session body
without the Kaggle UI:

```bash
docker build -f scripts/kaggle/Dockerfile -t hrm-gears-twin-t4 .
docker run --gpus all --rm -v "$PWD/var/kaggle-harvest/local:/out" hrm-gears-twin-t4
```

This is a skeleton. Prefer Kaggle T4 x2 for the cited harvest.

## Why not leave it up

You cannot. The free tier is a weekly quota, not a lease. Even if it
were a lease, paying for 24/7 T4s to fine-tune a 27M router would be
theatre. The paper trains this class of model in hours on one 16 GB
card (Wang et al., 2025). Dual T4s are luxury for batch size and
ablations, not a reason to keep silicon warm.
