# Architecture

## What this is not

This is not a Transformer. It is not a distilled LLM. It is not chain-of-thought
with a smaller context window.

hrm-gear adapts Sapient Intelligence's **Hierarchical Reasoning Model**
(Wang et al., 2025) — a 27-million-parameter **dual-timescale recurrent**
network with an Adaptive Computation Time (ACT) wrapper — into a candidate
**discrete router** for a Hermes-style orchestrator.

Credit for the architecture, the training recipe, and the published
checkpoints belongs to the authors listed in [REFERENCES.md](REFERENCES.md).
What follows is a reading of *their* system, plus the mapping we are testing.

## Why a non-Transformer

A Transformer decoder generates by attending over a growing token sequence.
Deep "reasoning" in that family is almost always **unrolled in language**:
chain-of-thought. That is expensive, brittle under distribution shift, and
poorly matched to a problem that is not open-ended generation.

Routing is a constrained hierarchical decision:

1. Observe a subtask (capability tags, context pressure, tool intensity, budget).
2. Compare it to a live model matrix.
3. Emit a discrete choice, cheaply, locally, repeatedly.

That is closer to search / planning than to next-token prediction. HRM was
designed for exactly that neighbourhood: Sudoku-Extreme, 30×30 Maze-Hard, and
ARC-AGI, trained from scratch on ~1k examples per task with no CoT supervision
(Wang et al., 2025).

## Dual timescales

`HierarchicalReasoningModel_ACTV1_Inner.forward` (`models/hrm/hrm_act_v1.py`)
maintains two recurrent states:

| State | Module | Role |
| --- | --- | --- |
| `z_H` | `H_level` (4 post-norm blocks) | Slow, abstract plan |
| `z_L` | `L_level` (4 post-norm blocks) | Fast iterative refinement |

One published config (`config/arch/hrm_v1.yaml`):

```
H_cycles = 2
L_cycles = 2
H_layers = L_layers = 4
hidden_size = 512
num_heads = 8
```

Per ACT step the inner loop is:

```
for H in range(H_cycles):
    for L in range(L_cycles):
        if not last (H, L):
            z_L ← L_level(z_L, z_H + x)
    if not last H:
        z_H ← H_level(z_H, z_L)
# one-step gradient pair
z_L ← L_level(z_L, z_H + x)
z_H ← H_level(z_H, z_L)
```

The no-grad inner iterations give computational depth. The final pair is the
only path that receives a gradient during training. That is deliberate: deep
unrolling without BPTT through every cycle.

Each block is attention + SwiGLU with RMSNorm *after* the residual
(`models/layers.py`). Attention uses RoPE. None of that makes it a GPT.
There is no causal mask on the puzzle grids (`causal=False`). The sequence
is a 2-D task encoding, not an autoregressive transcript.

## Adaptive Computation Time

The outer class `HierarchicalReasoningModel_ACTV1` is an ACT wrapper
(Graves, 2016, is the ancestor; HRM's halt head is a two-logit Q-learner).

- `q_head(z_H[:, 0])` → `(q_halt, q_continue)`
- Training may halt when `q_halt > q_continue`, with exploration.
- **Evaluation always runs `halt_max_steps` (16).** The comparison is
  recorded but does not stop the loop.

hrm-gear therefore reports two inference policies:

| Policy | Behaviour | Status |
| --- | --- | --- |
| A — paper eval | 16 ACT steps | reproduction |
| B — experimental | stop on first `q_halt > q_continue` | *not* a paper metric |

On a well-posed Sudoku, B wanted to halt at step 2. On constructed Maze/ARC
smoke inputs, the Q-head never crossed — expected for OOD encodings.

Per ACT step the inner recurrence applies `H_cycles * L_cycles` L-updates
and `H_cycles` H-updates. Sixteen eval steps ⇒ 64 L + 32 H.

## Puzzle embeddings

`CastedSparseEmbedding` (`models/sparse_embedding.py`) is a persistent
buffer, not an `nn.Embedding`. Sudoku/Maze use a single blank identifier.
ARC-2 ships **1,045,829** identifiers — that buffer alone is ~2.1 GiB
fp32 and dominates RSS (measured 3.5 GiB peak on the ARC-2 smoke).

A router does not need a million puzzle IDs. The adapted head will replace
this table with a compact encoding of the capability matrix.

## What we keep, what we change

Keep: H/L recurrence, ACT wrapper, 27M trunk, published initialisation.

Change (this repo):

- FlashAttention → SDPA on Apple Silicon (`hrm_gear/compat/flash_attn`).
- CUDA-only `evaluate.py` path → `hrm_gear.runtime` (CPU/MPS, strict load).
- Output head (future): discrete model ID + confidence + escalate, trained
  on the matrix in `config/model_matrix.v1.yaml`.

Do not claim the 27M puzzle weights already route LLMs. They do not. They
prove the *architecture* can do hierarchical discrete search from little
data. Adaptation is the remaining engineering.

## Related lines (not this codebase)

- **Tiny Recursive Models (TRM)** — a smaller recursive-refinement cousin
  discussed in the same design conversation. Not used here.
- **RouteLLM / FrugalGPT / cascade routers** — Transformer-on-Transformer
  routing. Complementary literature; different compute envelope.
- **FlashAttention** — I/O-aware exact attention on NVIDIA. Training
  dependency upstream; not present at inference on this machine.
