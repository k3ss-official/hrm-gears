# Phase 1 matrix by lane — frozen 2026-08-27

Source: `config/matrix.exploded.v1.yaml`. Reality recomputed from α=0.55, β=0.25.
Working set only (locked vendors). Not the full 300+ Portal catalog.

Algorithm: `docs/algorithm-phase1.md`. Chooser: `scripts/routing_data/policy_nested.py`.

## subscription

| id | vendor | floor | $/M in+out | claim | bench | offset | reality | tools | vision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `nous-longcat-2` | nous_portal | 2 | 0.00 | 0.78 | 0.68 | -0.15 | 0.688 | true | false |
| `nous-hy3` | nous_portal | 1 | 0.00 | 0.55 | 0.42 | +0.10 | 0.504 | true | false |
| `go-hy3` | opencode_go | 1 | 0.09 | 0.50 | 0.40 | +0.15 | 0.482 | true | false |
| `nous-deepseek-v4-flash` | nous_portal | 2 | 0.15 | 0.70 | 0.62 | +0.15 | 0.693 | true | false |
| `go-glm53-flash` | opencode_go | 2 | 0.32 | 0.72 | 0.64 | +0.10 | 0.701 | true | false |
| `nous-nemotron-3-super` | nous_portal | 2 | 0.39 | 0.72 | 0.52 | +0.05 | 0.622 | true | false |
| `nous-hermes4-405b` | nous_portal | 2 | 0.46 | 0.70 | 0.58 | +0.20 | 0.684 | true | false |
| `go-ds-v4-flash` | opencode_go | 2 | 0.88 | 0.70 | 0.62 | +0.15 | 0.693 | true | false |
| `go-gpt56-luna` | opencode_go | 2 | 1.40 | 0.78 | 0.68 | +0.10 | 0.750 | true | true |
| `oai-gpt54-nano` | openai_oauth | 1 | 1.45 | 0.60 | 0.50 | +0.10 | 0.570 | true | true |
| `go-longcat-2` | opencode_go | 2 | 1.50 | 0.78 | 0.68 | -0.10 | 0.700 | true | false |
| `nous-qwen38` | nous_portal | 2 | 2.38 | 0.74 | 0.66 | +0.05 | 0.708 | true | false |
| `nous-glm-52` | nous_portal | 3 | 2.98 | 0.80 | 0.70 | +0.10 | 0.770 | true | false |
| `nous-nemotron-3-ultra` | nous_portal | 3 | 3.36 | 0.80 | 0.46 | -0.25 | 0.550 | true | false |
| `oai-gpt54-mini` | openai_oauth | 2 | 5.25 | 0.72 | 0.62 | +0.10 | 0.690 | true | true |
| `go-glm53` | opencode_go | 3 | 5.80 | 0.82 | 0.72 | +0.05 | 0.777 | true | false |
| `oai-gpt56-luna` | openai_oauth | 2 | 7.00 | 0.78 | 0.68 | +0.10 | 0.750 | true | true |
| `go-grok-46` | opencode_go | 3 | 8.00 | 0.88 | 0.75 | +0.00 | 0.808 | true | true |
| `go-qwen38-max` | opencode_go | 3 | 8.00 | 0.86 | 0.74 | -0.05 | 0.782 | true | false |
| `nous-gemini-31-pro` | nous_portal | 3 | 11.20 | 0.88 | 0.72 | +0.00 | 0.792 | true | true |
| `oai-gpt56-terra` | openai_oauth | 3 | 17.50 | 0.88 | 0.76 | +0.00 | 0.814 | true | true |
| `go-kimi-k3` | opencode_go | 3 | 18.00 | 0.90 | 0.78 | -0.15 | 0.797 | true | false |
| `nous-gpt55` | nous_portal | 3 | 28.00 | 0.92 | 0.73 | -0.05 | 0.803 | true | true |
| `oai-gpt56-sol` | openai_oauth | 4 | 35.00 | 0.95 | 0.82 | +0.05 | 0.891 | true | true |
| `nous-fable5` | nous_portal | 4 | 48.00 | 0.98 | 0.88 | -0.10 | 0.900 | true | true |
| `oai-gpt55-pro` | openai_oauth | 4 | 210.00 | 0.97 | 0.93 | -0.20 | 0.898 | true | true |

## api_free

| id | vendor | floor | $/M in+out | claim | bench | offset | reality | tools | vision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `or-glm52-free` | openrouter | 2 | 0.00 | 0.80 | 0.70 | +0.15 | 0.782 | true | false |
| `or-laguna-s21-free` | openrouter | 2 | 0.00 | 0.74 | 0.64 | +0.10 | 0.710 | true | false |
| `or-minimax-m3-free` | openrouter | 2 | 0.00 | 0.72 | 0.62 | +0.05 | 0.677 | true | true |
| `nv-super-free` | nvidia_api | 2 | 0.00 | 0.72 | 0.52 | +0.00 | 0.610 | true | false |
| `nv-nano-omni-free` | nvidia_api | 2 | 0.00 | 0.70 | 0.44 | +0.10 | 0.582 | true | true |
| `nv-ultra-free` | nvidia_api | 2 | 0.00 | 0.80 | 0.46 | -0.20 | 0.563 | true | false |
| `or-nemotron-ultra-free` | openrouter | 2 | 0.00 | 0.80 | 0.46 | -0.20 | 0.563 | true | false |
| `or-gemma4-31b-free` | openrouter | 2 | 0.00 | 0.60 | 0.47 | +0.05 | 0.541 | true | true |
| `nv-lightning-free` | nvidia_api | 2 | 0.00 | 0.75 | 0.40 | -0.20 | 0.507 | true | false |
| `zen-glm47-free` | opencode_zen | 1 | 0.00 | 0.50 | 0.40 | +0.00 | 0.445 | true | false |
| `or-free-router` | openrouter | 1 | 0.00 | 0.50 | 0.35 | -0.10 | 0.392 | true | true |

## api_paid_non_frontier

| id | vendor | floor | $/M in+out | claim | bench | offset | reality | tools | vision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `nv-lightning-paid` | nvidia_api | 2 | 0.28 | 0.75 | 0.40 | -0.15 | 0.520 | true | false |
| `zen-gpt56-luna` | opencode_zen | 2 | 1.40 | 0.78 | 0.68 | +0.10 | 0.750 | true | true |
| `nv-ultra-paid` | nvidia_api | 3 | 4.20 | 0.80 | 0.46 | -0.25 | 0.550 | true | false |
| `zen-claude-sonnet-45` | opencode_zen | 3 | — | 0.80 | 0.70 | +0.05 | 0.757 | true | true |
| `zen-kimi-k2` | opencode_zen | 2 | — | 0.70 | 0.62 | +0.05 | 0.668 | true | false |
| `or-mid` | openrouter | 2 | — | 0.70 | 0.60 | +0.00 | 0.645 | true | false |
| `zen-big-pickle` | opencode_zen | 2 | — | 0.55 | 0.48 | +0.10 | 0.537 | true | false |

## api_paid_frontier

| id | vendor | floor | $/M in+out | claim | bench | offset | reality | tools | vision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `zen-gpt56-sol` | opencode_zen | 4 | 24.00 | 0.95 | 0.82 | +0.05 | 0.891 | true | true |
| `zen-fable5` | opencode_zen | 4 | 60.00 | 0.98 | 0.88 | -0.10 | 0.900 | true | true |
| `zen-opus5` | opencode_zen | 4 | — | 0.99 | 0.90 | -0.05 | 0.928 | true | true |
| `or-frontier` | openrouter | 4 | — | 0.95 | 0.85 | -0.10 | 0.870 | true | true |
