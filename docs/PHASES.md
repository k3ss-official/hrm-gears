# hrm-gears phases — 2026-08-26 night pack

Owner: Tony. Hands tonight: this session. Repo: `anwhelan01/hrm-gears`.
Gym Kaggle: `mrvibecoder` (discovery only). Main Kaggle: do not touch until Phase C is green.

## Done (receipts)

- Routing JSONL v1 published: `data/routing/v1/train.jsonl` (2696) + `held_out.jsonl` (304).
- Generator / gate already in repo:
  - `python scripts/routing_data/generate.py --n 3000`
  - `python scripts/routing_data/validate.py --strict`
- M4 smokes (Sudoku / Maze / ARC-2 ACT) previously PASS on MPS.
- Gym API CPU lap **COMPLETE** 2026-08-26T20:50Z:
  - kernel `mrvibecoder/hrm-gear-api-ping-cpu`
  - output `harvest/ping.json` pulled via CLI
  - GPU hours burned: **0**

## Phase A — gym API lock (account 2 only)

Goal: every CLI verb we need is boring.

| Lap | Accelerator | Pass when |
| --- | --- | --- |
| A0 CPU ping | none | **PASS** (done) |
| A1 GPU inventory | `NvidiaTeslaT4` | `harvest/smi.json` shows card names + count. Record whether we got 1×T4, 2×T4, or P100 |
| A2 stop drill | same | UI Stop (CLI cannot cancel a live session). Confirm quota sidebar moved by wall-clock only |
| A3 collect drill | — | `kaggle kernels output <slug> -p var/kaggle-harvest/<run>` |

Do not train on A1. Two minutes of `nvidia-smi` then stop.

## Phase B — trainer exists (code, CPU first)

Goal: `--train-routing` is no longer exit 3.

- v0 (this pack): bag-of-tags linear head on JSONL labels. Proves data contract + metrics. Runs on CPU/MPS in minutes. **Not** HRM adaptation.
- v1 (next code drop): classification head on frozen / partially-frozen HRM `z_H`, start from published 27M ckpt. This is the T4 job.

## Phase C — gym T4 train burst (account 2)

1. Pack (`scripts/kaggle/pack.py`).
2. Push notebook that runs v0 then, when v1 lands, v1.
3. Write `/kaggle/working/harvest/{MANIFEST,metrics,ckpt}`.
4. `kernels output` pull.
5. Stop session. Revoke gym token if it has been in a thread.

## Phase D — main account, clinical

Only after C harvest shows `t4_x2_seen: true` **and** held-out accuracy is logged.
Fresh token. One committed Save & Run All. Stop. Revoke.

## Hard rules

- Title must slug-match kernel id or Kaggle rewrites the slug (A0 lesson).
- Status the **URL** slug, not the metadata `id` we wished for.
- Custom keywords are often rejected. Don't depend on them.
- CLI cannot cancel a session and cannot read weekly quota. UI or MCP for those two.
- `T4 x2` is a UI/session fact. Confirm in-notebook. Do not trust `enable_gpu: true` alone.
- No secrets in git. Tokens live in env / `~/.kaggle/access_token` with mode 600.
