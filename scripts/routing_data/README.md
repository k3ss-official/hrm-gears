# Routing data scripts

Labels are computed by `policy.py` against `config/model_matrix.v1.yaml`.
Prose in templates never overrides the chosen model.

```bash
# regenerate the published allotment
python scripts/routing_data/generate.py --n 3000

# coverage gates (cell floor, per-model floor, escalation rate)
python scripts/routing_data/validate.py --strict
```

| File | Role |
| --- | --- |
| `policy.py` | cheapest-sufficient chooser + forced escalation |
| `templates.py` | synthetic / adversarial / negative stems |
| `generate.py` | emit `data/routing/v1/{train,held_out}.jsonl` |
| `validate.py` | ASK v1 gates |

V1 drop already on disk (3000 rows). Do not regenerate unless the matrix or schema changes.

Trainer that consumes this data: `scripts/kaggle/train_routing.py` (v0 tag head).
