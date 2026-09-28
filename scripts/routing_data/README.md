# Routing data scripts

Labels are computed by `policy.py` against `config/model_matrix.v1.yaml`.
Prose in templates never overrides the chosen model.

```bash
pip install -e ".[dev]"   # pyyaml + pytest

# regenerate the published allotment
python scripts/routing_data/generate.py --n 3000

# coverage gates (cell floor, per-model floor, escalation rate) -- flat matrix
python scripts/routing_data/validate.py --strict

# schema + evidence-citation gate -- exploded matrix (informational by
# default; --strict also fails on missing offset_evidence)
python scripts/routing_data/validate_exploded_matrix.py

# full pytest suite (tests/ at repo root, covers this dir + scripts/kaggle)
pytest
```

| File | Role |
| --- | --- |
| `policy.py` | flat-matrix cheapest-sufficient chooser + forced escalation (17 models, `config/model_matrix.v1.yaml`) — trains today's published JSONL labels |
| `policy_nested.py` | I → T → E chooser on the exploded matrix (48 models, `config/matrix.exploded.v1.yaml`) — `docs/algorithm-phase1.md` is its frozen spec |
| `_build_exploded_matrix.py` | one-shot, reality-verified transcription of `docs/matrix-phase1-by-lane.md` into `config/matrix.exploded.v1.yaml`; not part of the runtime pipeline, regenerate via this if the source table changes |
| `validate_exploded_matrix.py` | schema + invariant + evidence-citation gate for the exploded matrix (companion to `validate.py`, which only covers the flat one) |
| `free_lunch_tax.py` | whitepaper §4's τf/effective-cost formula, implemented and tested but deliberately **not wired into `policy_nested.py`** — see its module docstring for why |
| `templates.py` | synthetic / adversarial / negative stems |
| `generate.py` | emit `data/routing/v1/{train,held_out}.jsonl` |
| `validate.py` | ASK v1 gates (flat matrix) |

V1 drop already on disk (3000 rows). Do not regenerate unless the matrix or schema changes.

Trainer that consumes this data: `scripts/kaggle/train_routing.py` (v0 tag head;
softmax/loss are menu-masked to each row's `available_models` as of 2026-08-27).

Two escalation concepts exist in this repo and are easy to conflate — they
are unrelated: `policy.py`'s `forced_escalation()` is a flat-matrix,
tag-only statistic (`validate.py --strict`'s `escalation_pct` — 89.65% on
the train split, 89.8% on train+held combined; the CLI prints both as
`gates_train`/`gates_all`, gated as a ≥15% **floor**). `policy_nested.py`'s `choose()` has a
separate confidence-based one-lane-climb escalation gated at
`confidence_tau=0.62` — empirically, across the full capability-tag space
against the current exploded matrix, this one never fires (see
`tests/test_policy_nested.py`). Neither number is the other; see
`docs/architecture-decision-v2.md` §6.4 for the full correction.
