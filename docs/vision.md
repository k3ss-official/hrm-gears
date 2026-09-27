# Vision

Status: intent, not built. Recorded 2026-09-27 from the project owner.
What exists today is marked as such; everything else is target.

## The picture

```
task        = the journey (the road)
objective   = the destination
models      = the gears (cogs of different sizes)
harness     = the rider
hrm-gears   = the derailleur
```

A task is not one gear's worth of work. A job might need frontier
strength for 17% of the road and a cheaper model for the rest. The road
has climbs, descents, straights and bends. One gear for the whole ride
overpays on the flat and still fails on the hills nobody saw coming.
The derailleur shifts as the road changes.

```
 START ━━━━━━━╱‾‾‾‾╲━━━━━━━━━━━━━━━╮━━━━━━━━╱‾‾╲━━━━ objective
 flat         climb  descent  flat  bend     flat climb flat
 small        big    small    small mid      small big  small
```

## Three parts

```
   SCOUT                     TEST RIDE                  DERAILLEUR
   what gears exist          where each gear slips      which gear, right now
   today, at what price      and who takes over         on this stretch of road
        │                          │                           ▲
        └──── gear box (matrix) ───┴───────────────────────────┘
```

### 1. Derailleur: shift along the road

Two steps, run on every stretch, not once per task:

1. **Read the road.** Subtask text → capability tags (`reasoning_depth`,
   `tool_use`, `stakes`, `context_pressure`, `domain`). Closed label
   space. This is the learned part and the HRM candidate's job
   (Laya-style typed head is the comparison).
2. **Pick the gear.** Tags + available models → model id. Deterministic.
   Already built: `scripts/routing_data/policy.py`.

The derailleur also **splits stretches**. If the harness hands over a
subtask that hides a hill, the derailleur finds it and splits there
rather than paying frontier price for the whole stretch. HRM's dual
timescale (`z_H` slow / `z_L` fast) is the argument for HRM here: the
slow loop reads the road ahead, the fast loop reads the step under the
wheel.

Shifting rules a real derailleur has:

- **Never shift under load.** No model switch mid-tool-loop or across
  non-portable provider state. (Stated in `routing.md`; not enforced.)
- **Don't shift for a pebble.** A switch costs context re-load, cache
  loss and latency. Only shift when the saving beats that cost.
- **Unsure → one gear up.** Low confidence on any tag climbs one lane
  (`algorithm-phase1.md`, τ = 0.62).

### 2. Scout: keep the gear box current

Vendors (e.g. Nvidia) and aggregators (OpenCode Zen / Go, Nous Portal,
OpenRouter) change their offer on a near-daily basis: free windows,
time-boxed deals, new models, retirements. Model news (e.g. Testing
Catalog) moves faster than any hand-edited matrix.

The scout runs on a schedule (daily, target near-hourly):

- gather: vendor/aggregator catalogues and pricing, deal/free-window
  announcements, retirement notices, model news
- map: each finding onto a matrix id (new, changed price, changed lane,
  retired)
- stamp: every deal carries a start and an **expiry**; expired deals
  drop out without a human
- emit: a versioned matrix delta, never a silent overwrite

Outcome: the derailleur chooses from the latest models *and* what is
hot, cheap or free right now.

### 3. Test ride: know where each gear slips

Vendor benchmarks are claims. Before a model enters the gear box it is
audited once, and again when it is promoted or added permanently:

- **strengths / weaknesses** by capability tag
- **drop-off point**: where it degrades, breaks or fails (depth,
  context length, tool-loop length, domain)
- **true cost of free**: rate limits, queueing, context caps, prompt
  retention / training use, silent downgrades
- **takeover model**: when this gear slips, which gear finishes the job
  so the task completes without a restart

The takeover map is what makes shifting seamless instead of a retry.

## Exists vs missing

| Piece | Today |
| --- | --- |
| Gear box (matrix v1) | `config/model_matrix.v1.yaml`, hand-frozen |
| Exploded matrix (prices, flags, scores) | **stub only** in git; full YAML never committed |
| Gear pick (tags → model) | built, deterministic: `policy.py`, `policy_nested.py` |
| Reality score (claim vs bench vs hype) | designed in `algorithm-phase1.md`; frozen, not live |
| Road reader (text → tags) | missing; training data ships tags pre-filled |
| Stretch splitting | missing |
| Shift rules (load, pebble) | stated, not enforced; no switch-cost model |
| Scout | missing |
| Test ride / drop-off / takeover map | missing |
| Real traces | missing (25% slot in `routing.md` empty) |

## Landscape (checked 2026-09-27)

Per-prompt routers exist: OpenRouter Auto Router (moved off Not Diamond
to a 7-day community spend signal, Aug 2026), Not Diamond, Martian,
LiteLLM, RouteLLM. Free-model trackers exist but cover OpenRouter only.
Not found: mid-task shifting, cross-vendor deal scouting that includes
subscriptions, or owner-audited failure points with a takeover map.
That combination is the bet. Two searches is not proof it is unoccupied.

- https://openrouter.ai/docs/guides/routing/routers/auto-router
- https://aireiter.com/blog/openrouter-auto-router-guide
- https://www.braintrust.dev/articles/best-llm-routers-2026
- https://freellmrouter.com/
