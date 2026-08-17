# Compute — Twin-T4 harvest

The M4 Mac mini is the right machine for **bring-up**. It is the wrong
machine for **adaptation**. There is no NVIDIA GPU. Sixteen gigabytes of
unified memory is enough to load the 27M trunk and run ACT smokes; it is
not a training cluster, and we will not rent one to sit idle.

Training therefore uses a named pattern: **Twin-T4 harvest**.

## What Twin-T4 harvest is

Kaggle Notebooks expose a free accelerator labelled **GPU T4 x2**:

| | |
| --- | --- |
| Cards | 2 × NVIDIA Tesla T4 |
| VRAM | 16 GB per card (~32 GB combined) |
| Host RAM | ~29 GB on current T4 notebooks |
| Quota | on the order of **30 GPU hours per week**, not a month-long reservation |
| Session cap | typically 9–12 hours, then the VM dies |

Cite: Kaggle's own notebook docs and the T4 x2 product note
(<https://www.kaggle.com/docs/notebooks>). Quota is weekly and finite.
Leave a session running and you burn the week on idle CUDA context.

Twin-T4 harvest is **just-in-time dual-T4**:

1. **Pack** — a single, replayable bundle (this repo + data snapshot +
   matrix version + training script). Think image or notebook + dataset,
   not a pet VM.
2. **Spin** — start a T4 x2 session only when a run is queued.
3. **Run** — smoke, then fine-tune / head-train, checkpointing aggressively
   because the session *will* be killed.
4. **Harvest** — pull weights, metrics, logs, and the exact git SHA that
   produced them off the box before teardown.
5. **Kill** — stop the session. No standing GPU. Next week, pack again
   from the harvested artifact, not from folklore.

The durable object is the **artifact**, not the machine. The M4 keeps the
repo, the matrix, and the harvested runs. Kaggle is a burst pair you
borrow and give back.

## Why not leave it up

You cannot. The free tier is a quota, not a lease. Even if it were a
lease, paying for 24/7 T4s to fine-tune a 27M router would be theatre.
The paper trains this class of model in hours on one 16 GB card
(Wang et al., 2025). Dual T4s are luxury for batch size and ablations,
not a reason to keep silicon warm.

Colab T4 is overflow only (quota is less predictable). Oracle Always Free
is ARM/CPU and is out for this job.

## What already ran locally (PASS)

Cursory inference on the M4, PyTorch 2.13.0 MPS, SDPA stand-in. Not
paper-task test-set scores. Strict `load_state_dict`, ACT loop, in-vocab
outputs. Details in [experiments.md](experiments.md).

| Check | Result |
| --- | --- |
| Sudoku-extreme weights, 16-step ACT | **PASS** |
| Maze-30x30-hard weights, 16-step vs early-exit | **PASS** (Q-head never crossed on the constructed board) |
| ARC-2 weights, 16-step vs early-exit | **PASS** (same; RSS ~3.5 GiB from the puzzle-ID table) |

That is as far as a machine with no CUDA is allowed to take the story.
The next numbers that matter come off a harvested Twin-T4 run.
