# Routing examples v1.0

Publishable MVP allotment data for the cheapest-viable router.
Not training code. Not weights. `outcome` is null — no live Hermes traces yet.

## Cite

- Matrix: `config/model_matrix.v1.yaml` (`matrix_version: "1.0"`).
- Policy: `scripts/routing_data/policy.py`.
- Schema version: `1.0`.
- Generator: `python scripts/routing_data/generate.py`.
- Gate: `python scripts/routing_data/validate.py --strict`.

## Priority rule

When several models satisfy the tags, pick the highest-priority
(lowest-tier) option: `free → non_frontier_sub → frontier_sub →
non_frontier_api → frontier_api`. Within a tier, YAML order is
cheaper / faster. `chosen_model` is that function applied to
`available_models`. Prose never overrides the label.

## Counts

- total: 3000
- train.jsonl: 2696
- held_out.jsonl: 304 (10% id-hash split, 0 description leakage)

### By label_source

- adversarial: 480 (16.0%)
- negative: 210 (7.0%)
- synthetic: 2310 (77.0%)

### By chosen_tier

- free: 289 (9.6%)
- frontier_api: 246 (8.2%)
- frontier_sub: 1789 (59.6%)
- non_frontier_api: 369 (12.3%)
- non_frontier_sub: 307 (10.2%)

## Coverage gates (ASK v1 drop)

- cell floor: 20 per reasoning_depth × tool_use × stakes
- model floor: 15 as chosen_model
- escalation: 89.8% (need ≥ 15%)
- cells: PASS
- models: PASS
- escalation: PASS

### Cell table

| reasoning_depth | tool_use | stakes | n |
| --- | --- | --- | ---: |
| deep | heavy | high | 366 |
| deep | heavy | low | 71 |
| deep | heavy | medium | 150 |
| deep | light | high | 150 |
| deep | light | low | 71 |
| deep | light | medium | 70 |
| deep | none | high | 150 |
| deep | none | low | 71 |
| deep | none | medium | 71 |
| medium | heavy | high | 150 |
| medium | heavy | low | 71 |
| medium | heavy | medium | 70 |
| medium | light | high | 150 |
| medium | light | low | 71 |
| medium | light | medium | 190 |
| medium | none | high | 70 |
| medium | none | low | 71 |
| medium | none | medium | 71 |
| shallow | heavy | high | 70 |
| shallow | heavy | low | 71 |
| shallow | heavy | medium | 70 |
| shallow | light | high | 70 |
| shallow | light | low | 71 |
| shallow | light | medium | 70 |
| shallow | none | high | 70 |
| shallow | none | low | 353 |
| shallow | none | medium | 71 |

### chosen_model counts

| id | n |
| --- | ---: |
| free-opencode-zen | 239 |
| free-openrouter | 25 |
| free-nous | 25 |
| nous-deepseek | 138 |
| nous-nemotron | 42 |
| nous-qwen | 44 |
| nous-hy3 | 43 |
| openai-nonfrontier | 40 |
| openai-gpt56-sol | 1420 |
| nous-fable5 | 123 |
| nous-gemini | 123 |
| opencode-go-frontier | 123 |
| openrouter-mid | 123 |
| nvidia-nemotron | 123 |
| opencode-zen-paid | 123 |
| openrouter-frontier | 123 |
| nvidia-frontier | 123 |

## Schema

One JSON object per line. Mandatory fields are exactly those in the
ASK: `schema_version`, `id`, `matrix_version`, `subtask`,
`context_signals`, `available_models`, `chosen_model`, `chosen_tier`,
`confidence`, `rationale_tags`, `label_source`, `outcome`.

Real Hermes traces (25% in the long-run mix) are **not** in this drop.
That slot stays empty until traces exist. Adversarial + negative +
synthetic fill the file so it is trainable without lying about source.
