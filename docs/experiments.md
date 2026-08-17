# Experiments

All numbers below are **inference smoke tests** on constructed inputs, not
paper-task test-set accuracy. They answer: do the published weights load
strictly, does the ACT loop run on MPS, and does the Q-head ever fire?

Device: M4 Mac mini, PyTorch 2.13.0 MPS, SDPA shim. bfloat16 forward dtype
as in `HierarchicalReasoningModel_ACTV1Config.forward_dtype`.

## Strict load

| Checkpoint | vocab | seq | puzzle IDs | params | result |
| --- | --- | --- | --- | --- | --- |
| `HRM-checkpoint-sudoku-extreme` | 11 | 81 | 1 | 27,275,266 | strict OK |
| `HRM-checkpoint-maze-30x30-hard` | 6 | 900 | 1 | 27,270,146 | strict OK |
| `HRM-checkpoint-ARC-2` | 12 | 900 | 1,045,829 | 27,276,290 | strict OK |

Missing / unexpected keys: none, after stripping `_orig_mod.` and `model.`.

## Sudoku (easy 9×9, not from the 1k-extreme train split)

Policy A only (`halt_max_steps = 16`).

| | |
| --- | --- |
| logits | `(1, 81, 11)` |
| first `q_halt > q_continue` | **step 2** |
| ACT steps executed | 16 (eval policy) |
| L / H updates | 64 / 32 |
| latency | 3.43 s (cold) |
| peak RSS | 513 MiB |
| givens preserved | yes |
| decoded grid | valid completed Sudoku |

The Q-head wanted to stop at step 2. Eval still ran 16. That is upstream
behaviour, not a bug in the harness.

## Maze 30×30 and ARC-2 (constructed encodings)

| task | mode | first `q_halt>q_cont` | steps | L | H | lat s | speedup | peak RSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| maze | A 16-step | none | 16 | 64 | 32 | 1.666 | 1.00× | 513 MiB |
| maze | B early-exit | none | 16 | 64 | 32 | 1.664 | 1.00× | 513 MiB |
| ARC-2 | A 16-step | none | 16 | 64 | 32 | 1.658 | 1.00× | 3544 MiB |
| ARC-2 | B early-exit | none | 16 | 64 | 32 | 1.659 | 1.00× | 3544 MiB |

Outputs stayed in-vocab. Early-exit could not win time because the Q-head
never crossed on these synthetic boards. ARC RSS is the puzzle-embedding
table (~2.1 GiB fp32) plus activations.

Maze tokens follow Sapient's `"# SGo"` map. ARC tokens follow PAD/EOS/colour
padding in `dataset/build_arc_dataset.py`. These are *format-valid* smokes,
not official test puzzles. Do not cite them as Maze-Hard or ARC-AGI scores.

## What this does *not* measure

- Test-set exact accuracy on Sudoku-Extreme / Maze-Hard / ARC-AGI-2.
- FlashAttention latency.
- Router quality. There is no trained routing head yet.

## Next measurements that would change our mind

1. Fine-tune the 27M trunk on 400–800 labelled routes; report top-1 vs
   cheapest-viable oracle on a held-out Hermes mix.
2. Compare Q-head halt step on *real* Maze/ARC eval items, not constructed
   boards.
3. CUDA FA2 run of the same smokes, to bound the SDPA tax.
