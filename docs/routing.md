# Routing target

## Job

Hermes is the first rider. The harness is the bicycle. Published LLMs are
the gears. HRM is being evaluated as the **derailleur**: a local, 27M,
hierarchical decision engine that, given a subtask annotation and
`config/model_matrix.v1.yaml`, returns the cheapest model that can still
do the work.

Hermes ([@NousResearch](https://x.com/NousResearch)) is the design-centre install. Nothing in the
matrix or the planned head is Hermes-specific. Any harness that can tag a
subtask and switch model id can sit on the same unit.

The logic does not have to be comprehensive. A subtask arrives with
tags. A trained parameterisation of the matrix allots it to a model id.
Escalate if confidence is low. That is supervision, not composition.

This is not prestige routing. The hard rule, locked by the project owner:

> When several models satisfy the required tags, pick the highest-priority
> (lowest-tier number) option. Within a tier, cheaper / faster wins.

## Why HRM for that job

| Router requirement | HRM property |
| --- | --- |
| Discrete choice, not prose | ACT Q-head is already a 2-way halt/continue classifier |
| Hierarchical plan vs step | `z_H` / `z_L` dual timescale |
| Local, always on | 27M; MPS inference fits in <1 GiB without ARC IDs |
| Few-shot adaptation | paper trains puzzle tasks from ~1k examples |
| No CoT tax on the decision | single forward, deep recurrence |

Limitations we are not hand-waving:

- Off-the-shelf weights are **symbolic puzzle solvers**, not language
  classifiers. Adaptation on real traces is mandatory.
- Continuity: never hop mid-tool-loop or across non-portable provider state.
- Low-confidence routes must escalate. The 27M unit proposes; Hermes accepts.

## Input / output contract (v1)

Input (to be packed into the HRM sequence later):

- subtask text or a frozen embedding of it
- capability tags (`reasoning_depth`, `tool_use`, `domain`,
  `context_pressure`, `stakes`) — v1 JSONL key is `tool_use`, not
  `tool_intensity`
- snapshot of the matrix (tier, cost, windows, hard constraints)
- session signals (remaining budget, last failure)

Output:

- `chosen_model` (stable ID from the matrix)
- `confidence`
- `escalate` flag
- `rationale_tags` (for data, not for the user)

`matrix_version` is carried on every example. v1.0 is
`config/model_matrix.v1.yaml`.

## Data mix

v1 drop lives at [`data/routing/v1/`](../data/routing/v1/). Real Hermes
traces are **not** in this drop (that 25% slot stays empty until traces
exist). Generator: `scripts/routing_data/generate.py`. Gate:
`scripts/routing_data/validate.py --strict`.

| Source | share (this drop) | purpose |
| --- | --- | --- |
| Synthetic from the matrix | ~77% (55% combo + fill) | combinatorial coverage |
| Real Hermes traces | 0% (deferred) | actual outcomes |
| Adversarial / edge | ~16% | force escalations |
| Negatives | ~7% | teach when *not* to pick a model |

ASK v1 gates (this drop): ≥20 per `reasoning_depth × tool_use × stakes`
cell; every matrix id chosen ≥15 times; ≥15% forced tier escalations.
Stricter later gates (≥30 / ≥40) wait for traces.

## Training compute (intended, not run)

Paper-scale 27M training is hours on one 16 GB GPU. Plan: Kaggle
**GPU T4 x2** as primary, Colab T4 as overflow. The M4 can do it; we
refuse to burn it on a one-shot adaptation. Oracle Always Free is ARM/CPU
and is out.

Start from the published 27M checkpoint. Do not train from scratch.
Replace or sit a classification head on top of `z_H`; freeze early
blocks first; watch for collapse of the original hierarchical behaviour.

## Integration sketch

After Hermes decomposes a goal, before `call_llm` / `delegate_task`:

1. Annotate the subtask.
2. Run the adapted HRM (auxiliary slot, local process).
3. Apply session-affinity guards.
4. Log decision + outcome into the experience store.
5. Fall back to a rule/LLM classifier if confidence is low or the unit
   is offline.

Grok Build 4.6 on this machine (parallel subagents, worktrees, named
sessions, headless `-p`) is the intended factory for synthetic traces.
That is a consumer of this repo, not a dependency of it.
