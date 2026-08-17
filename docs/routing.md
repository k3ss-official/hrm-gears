# Routing target

## Job

Hermes is the rider. The harness is the bicycle. Published LLMs are the
gears. HRM is being evaluated as the **derailleur**: a local, 27M,
hierarchical decision engine that, given a subtask annotation and
`config/model_matrix.v1.yaml`, returns the cheapest model that can still
do the work.

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
- capability tags (`reasoning_depth`, `tool_intensity`, `domain`,
  `context_pressure`, `stakes`, `latency_budget`)
- snapshot of the matrix (tier, cost, windows, hard constraints)
- session signals (remaining budget, last failure)

Output:

- `chosen_model` (stable ID from the matrix)
- `confidence`
- `escalate` flag
- `rationale_tags` (for data, not for the user)

`matrix_version` is carried on every example. v1.0 is
`config/model_matrix.v1.yaml`.

## Data mix (not yet generated)

| Source | share | purpose |
| --- | --- | --- |
| Synthetic from the matrix | 55% | combinatorial coverage |
| Real Hermes traces | 25% | actual outcomes |
| Adversarial / edge | 15% | force escalations |
| Negatives | 5%+ | teach when *not* to pick a model |

Coverage gates before a training run: ≥30 positives per
`reasoning_depth × tool_use × stakes` cell; every model ID chosen ≥40
times; ≥15% forced tier escalations.

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
