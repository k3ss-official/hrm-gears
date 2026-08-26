# Kaggle gym API — tested process

Account under test: `mrvibecoder` (gym). Auth: `KAGGLE_API_TOKEN=KGAT_…` (Kaggle CLI 2.2.4, `auth_method: ACCESS_TOKEN`).
Main account: out of scope for these laps.

## A0 receipt (2026-08-26)

```
kaggle kernels push -p <dir>
# warned: title did not resolve to id
# created: mrvibecoder/hrm-gear-api-ping-cpu   (not …/hrm-gear-api-ping)
status: RUNNING → COMPLETE (~30s)
kaggle kernels output mrvibecoder/hrm-gear-api-ping-cpu -p ./harvest
# got harvest/ping.json
```

`ping.json`:

```json
{
  "ok": true,
  "purpose": "api-ping-cpu",
  "python": "3.12.13",
  "cwd": "/kaggle/working",
  "has_kaggle_working": true
}
```

## Commands that worked

```bash
export KAGGLE_API_TOKEN=KGAT_…          # gym token only
kaggle --version                         # 2.2.4
kaggle kernels push -p DIR
kaggle kernels status OWNER/SLUG
kaggle kernels files OWNER/SLUG
kaggle kernels output OWNER/SLUG -p OUT
kaggle kernels list --mine -v
```

## Commands / surfaces that did not

| Need | Result |
| --- | --- |
| Status on metadata id after slug rewrite | `Permission kernels.get denied` |
| Custom kernel keywords | rejected |
| Cancel running session via CLI | no verb |
| Read weekly GPU quota via CLI | no verb (MCP `get_accelerator_quota` exists, this chat: Unauthenticated) |
| Guarantee T4 ×2 via `enable_gpu` | not guaranteed; confirm `nvidia-smi` |

## Metadata template that behaves

`id` **and** `title` must slug to the same string.

```json
{
  "id": "mrvibecoder/hrm-gear-api-ping-cpu",
  "title": "hrm-gear-api-ping-cpu",
  "code_file": "ping.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": true,
  "enable_gpu": false,
  "enable_internet": true
}
```

GPU lap: set `"enable_gpu": true` and push with `--accelerator NvidiaTeslaT4`. Then read cards from output, not from the flag.

## Loop we will repeat

```
PREP local notebook + metadata (CPU or GPU flag)
PUSH  kaggle kernels push -p DIR
WATCH kaggle kernels status OWNER/SLUG
COLLECT kaggle kernels output OWNER/SLUG -p var/kaggle-harvest/RUN
STOP  Kaggle UI → Stop session
```
