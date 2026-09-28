#!/usr/bin/env python3
"""One-shot generator for config/matrix.exploded.v1.yaml from the frozen
table in docs/matrix-phase1-by-lane.md (frozen 2026-08-27).

Not part of the runtime pipeline — this is a transcription tool, kept in
the repo so the YAML's provenance is auditable and re-derivable from the
frozen markdown table rather than being a hand-typed, unverifiable blob.

Every row's reality score is recomputed from alpha/beta and checked
against the table's own precomputed reality column (rounded to 3dp) —
a transcription error shows up as an assertion failure, not a silent
wrong number in the shipped config.
"""
from __future__ import annotations

import yaml

ALPHA = 0.55
BETA = 0.25
CONFIDENCE_TAU = 0.62
LANE_ORDER = ["subscription", "api_free", "api_paid_non_frontier", "api_paid_frontier"]

# Evidence backfill, 2026-08-27 overnight research pass (architecture-decision-v2.md
# §6.6): real citations for community_offset, found by independently researching each
# model's public reception and checking specifically whether real-world/community
# commentary discusses a gap between the model's benchmark/vendor claims and its
# real-world performance -- not just "is this a good model" in general. Only entries
# where that specific evidence *matches the existing offset's direction* are included
# here; models were also researched where evidence *contradicted* the existing offset
# (nous-hy3, nous-hermes4-405b, oai-gpt56-sol, zen-claude-sonnet-45) or was mixed/absent
# -- those are deliberately NOT given a citation here, because citing evidence that
# doesn't actually support the number would be worse than the original gap. See
# docs/offset-evidence-audit-2026-08-27.md for the full 42-model research writeup,
# including the contradicting and inconclusive cases, which still need a human decision.
EVIDENCE: dict[str, str] = {
    "nous-longcat-2": (
        "Hands-on testing found LongCat-2.0 'buggy and rough around the edges,' losing "
        "head-to-head to GLM-5.2 despite competitive benchmark scores (2026-08-27 research "
        "pass): https://aiprofitboardroom.com/blog/meituan-longcat-2-0/"
    ),
    "nous-deepseek-v4-flash": (
        "Independent testers reported tool-calling reliability held up better than expected "
        "for its price tier (2026-08-27 research pass): "
        "https://blog.kilo.ai/p/we-tested-deepseek-v4-pro-and-flash"
    ),
    "nous-glm-52": (
        "Topped Design Arena's blind human-preference test ~10 Elo ahead of Claude Fable 5, "
        "and beat Hy3/LongCat-2.0 in hands-on builds despite comparable or higher raw "
        "benchmarks (2026-08-27 research pass): https://www.layer3labs.io/guides/glm-5-2-review"
    ),
    "nous-nemotron-3-ultra": (
        "Independent browser-agent benchmark ranked it 11th of 11 models tested despite "
        "vendor 'agent orchestration' positioning (2026-08-27 research pass): "
        "https://www.webbrain.one/blog/nemotron3-ultra-openrouter-planner-benchmark"
    ),
    "nous-gpt55": (
        "Review reports teams seeing slower apps, higher bills, and subtle regressions "
        "despite stellar benchmark scores (2026-08-27 research pass): "
        "https://www.solopreneur.global/posts/gpt-5-5-real-world-performance-vs-marketing-claims-us"
    ),
    "go-glm53-flash": (
        "Before its identity was revealed, this model (as mystery 'Ox Alpha') became the "
        "week's most-used model on real agentic workloads, outperforming its apparent weight "
        "class (2026-08-27 research pass): "
        "https://blog.kilo.ai/p/ox-alpha-was-glm-53-flash-all-along"
    ),
    "go-ds-v4-flash": (
        "Hacker News users running it in production report it performing better than the pro "
        "tier and out-executing pricier models (2026-08-27 research pass): "
        "https://news.ycombinator.com/item?id=49119559"
    ),
    "go-longcat-2": (
        "Hands-on review: 'playable, but buggy and rough around the edges,' outperformed by "
        "GLM-5.2 head-to-head despite competitive benchmarks; moderate confidence, one other "
        "outlet framed adoption more favorably (2026-08-27 research pass): "
        "https://aiprofitboardroom.com/blog/meituan-longcat-2-0/"
    ),
    "go-kimi-k3": (
        "Analysis shows hallucination rate climbing alongside benchmark accuracy gains; "
        "practitioners want real long-session usage reports before trusting rankings "
        "(2026-08-27 research pass): "
        "https://kili-technology.com/blog/kimi-k3s-benchmarks-and-hallucinations----what-that-tells-us-about-ai-evaluation"
    ),
    "oai-gpt55-pro": (
        "Independent reviews describe it as underwhelming vs. its own marketing/benchmark "
        "claims in practice -- 'lazy execution style,' familiar failure modes (2026-08-27 "
        "research pass): "
        "https://www.solopreneur.global/posts/gpt-5-5-real-world-performance-vs-marketing-claims-us"
    ),
    "or-glm52-free": (
        "Hands-on report contrasts typical benchmark-chart hype with GLM-5.2 actually "
        "matching Claude-level code quality and shipping deployment-ready output on the "
        "first try (2026-08-27 research pass): "
        "https://dev.to/danielbergholz/testing-glm-52-on-opencode-im-impressed-1780"
    ),
    "or-free-router": (
        "OpenRouter's own docs position this router for learning/prototyping rather than "
        "production, flagging higher latency/availability/rate-limit variance; direction "
        "matches, exact magnitude not independently verified (2026-08-27 research pass): "
        "https://openrouter.ai/docs/guides/routing/routers/free-router"
    ),
    "nv-lightning-free": (
        "Hacker News hands-on coding test found it 'terrible,' going off the rails vs. dense "
        "alternatives despite its speed advantage (2026-08-27 research pass): "
        "https://news.ycombinator.com/item?id=49263340"
    ),
    "nv-lightning-paid": (
        "Same underlying model as the free-tier SKU; under-delivery evidence came from a "
        "general deployment rather than the rate-limited free endpoint specifically, so it "
        "reasonably extends here, though no paid-tier-specific report was found (2026-08-27 "
        "research pass): https://news.ycombinator.com/item?id=49263340"
    ),
    "zen-kimi-k2": (
        "Hands-on review found it matched/exceeded its own vendor SWE-bench claim in real "
        "coding tasks -- 93% success across 15 hands-on tasks vs. 69.2% vendor-reported "
        "benchmark (2026-08-27 research pass): "
        "https://medium.com/@leucopsis/kimi-k2-0905-review-cf12b026a7a4"
    ),
    "zen-gpt56-sol": (
        "Hands-on test building five real apps scored 2 perfect + 1 solid of 5; corroborated "
        "by a second independent review calling it one of OpenAI's largest practical "
        "upgrades (2026-08-27 research pass): "
        "https://promptslove.com/blog/my-honest-gpt-5-6-sol-review/"
    ),
    "zen-opus5": (
        "Multiple developers report reverting to Opus 4.8, calling Opus 5 'nerfed, not "
        "upgraded' despite benchmark scores comparable to GPT-5.6 Sol (2026-08-27 research "
        "pass): https://www.mindstudio.ai/blog/claude-opus-5-mixed-reception"
    ),
}

# (id, vendor, lane, ability_floor, cost_or_None, claim, bench, offset, tools, vision, expected_reality)
ROWS = [
    # --- subscription ---
    ("nous-longcat-2", "nous_portal", "subscription", 2, 0.00, 0.78, 0.68, -0.15, True, False, 0.688),
    ("nous-hy3", "nous_portal", "subscription", 1, 0.00, 0.55, 0.42, 0.10, True, False, 0.504),
    ("go-hy3", "opencode_go", "subscription", 1, 0.09, 0.50, 0.40, 0.15, True, False, 0.482),
    ("nous-deepseek-v4-flash", "nous_portal", "subscription", 2, 0.15, 0.70, 0.62, 0.15, True, False, 0.693),
    ("go-glm53-flash", "opencode_go", "subscription", 2, 0.32, 0.72, 0.64, 0.10, True, False, 0.701),
    ("nous-nemotron-3-super", "nous_portal", "subscription", 2, 0.39, 0.72, 0.52, 0.05, True, False, 0.622),
    ("nous-hermes4-405b", "nous_portal", "subscription", 2, 0.46, 0.70, 0.58, 0.20, True, False, 0.684),
    ("go-ds-v4-flash", "opencode_go", "subscription", 2, 0.88, 0.70, 0.62, 0.15, True, False, 0.693),
    ("go-gpt56-luna", "opencode_go", "subscription", 2, 1.40, 0.78, 0.68, 0.10, True, True, 0.750),
    ("oai-gpt54-nano", "openai_oauth", "subscription", 1, 1.45, 0.60, 0.50, 0.10, True, True, 0.570),
    ("go-longcat-2", "opencode_go", "subscription", 2, 1.50, 0.78, 0.68, -0.10, True, False, 0.700),
    ("nous-qwen38", "nous_portal", "subscription", 2, 2.38, 0.74, 0.66, 0.05, True, False, 0.708),
    ("nous-glm-52", "nous_portal", "subscription", 3, 2.98, 0.80, 0.70, 0.10, True, False, 0.770),
    ("nous-nemotron-3-ultra", "nous_portal", "subscription", 3, 3.36, 0.80, 0.46, -0.25, True, False, 0.550),
    ("oai-gpt54-mini", "openai_oauth", "subscription", 2, 5.25, 0.72, 0.62, 0.10, True, True, 0.690),
    ("go-glm53", "opencode_go", "subscription", 3, 5.80, 0.82, 0.72, 0.05, True, False, 0.777),
    ("oai-gpt56-luna", "openai_oauth", "subscription", 2, 7.00, 0.78, 0.68, 0.10, True, True, 0.750),
    ("go-grok-46", "opencode_go", "subscription", 3, 8.00, 0.88, 0.75, 0.00, True, True, 0.808),
    ("go-qwen38-max", "opencode_go", "subscription", 3, 8.00, 0.86, 0.74, -0.05, True, False, 0.782),
    ("nous-gemini-31-pro", "nous_portal", "subscription", 3, 11.20, 0.88, 0.72, 0.00, True, True, 0.792),
    ("oai-gpt56-terra", "openai_oauth", "subscription", 3, 17.50, 0.88, 0.76, 0.00, True, True, 0.814),
    ("go-kimi-k3", "opencode_go", "subscription", 3, 18.00, 0.90, 0.78, -0.15, True, False, 0.797),
    ("nous-gpt55", "nous_portal", "subscription", 3, 28.00, 0.92, 0.73, -0.05, True, True, 0.803),
    ("oai-gpt56-sol", "openai_oauth", "subscription", 4, 35.00, 0.95, 0.82, 0.05, True, True, 0.891),
    ("nous-fable5", "nous_portal", "subscription", 4, 48.00, 0.98, 0.88, -0.10, True, True, 0.900),
    ("oai-gpt55-pro", "openai_oauth", "subscription", 4, 210.00, 0.97, 0.93, -0.20, True, True, 0.898),
    # --- api_free ---
    ("or-glm52-free", "openrouter", "api_free", 2, 0.00, 0.80, 0.70, 0.15, True, False, 0.782),
    ("or-laguna-s21-free", "openrouter", "api_free", 2, 0.00, 0.74, 0.64, 0.10, True, False, 0.710),
    ("or-minimax-m3-free", "openrouter", "api_free", 2, 0.00, 0.72, 0.62, 0.05, True, True, 0.677),
    ("nv-super-free", "nvidia_api", "api_free", 2, 0.00, 0.72, 0.52, 0.00, True, False, 0.610),
    ("nv-nano-omni-free", "nvidia_api", "api_free", 2, 0.00, 0.70, 0.44, 0.10, True, True, 0.582),
    ("nv-ultra-free", "nvidia_api", "api_free", 2, 0.00, 0.80, 0.46, -0.20, True, False, 0.563),
    ("or-nemotron-ultra-free", "openrouter", "api_free", 2, 0.00, 0.80, 0.46, -0.20, True, False, 0.563),
    ("or-gemma4-31b-free", "openrouter", "api_free", 2, 0.00, 0.60, 0.47, 0.05, True, True, 0.541),
    ("nv-lightning-free", "nvidia_api", "api_free", 2, 0.00, 0.75, 0.40, -0.20, True, False, 0.507),
    ("zen-glm47-free", "opencode_zen", "api_free", 1, 0.00, 0.50, 0.40, 0.00, True, False, 0.445),
    ("or-free-router", "openrouter", "api_free", 1, 0.00, 0.50, 0.35, -0.10, True, True, 0.392),
    # --- api_paid_non_frontier ---
    ("nv-lightning-paid", "nvidia_api", "api_paid_non_frontier", 2, 0.28, 0.75, 0.40, -0.15, True, False, 0.520),
    ("zen-gpt56-luna", "opencode_zen", "api_paid_non_frontier", 2, 1.40, 0.78, 0.68, 0.10, True, True, 0.750),
    ("nv-ultra-paid", "nvidia_api", "api_paid_non_frontier", 3, 4.20, 0.80, 0.46, -0.25, True, False, 0.550),
    ("zen-claude-sonnet-45", "opencode_zen", "api_paid_non_frontier", 3, None, 0.80, 0.70, 0.05, True, True, 0.757),
    ("zen-kimi-k2", "opencode_zen", "api_paid_non_frontier", 2, None, 0.70, 0.62, 0.05, True, False, 0.668),
    ("or-mid", "openrouter", "api_paid_non_frontier", 2, None, 0.70, 0.60, 0.00, True, False, 0.645),
    ("zen-big-pickle", "opencode_zen", "api_paid_non_frontier", 2, None, 0.55, 0.48, 0.10, True, False, 0.537),
    # --- api_paid_frontier ---
    ("zen-gpt56-sol", "opencode_zen", "api_paid_frontier", 4, 24.00, 0.95, 0.82, 0.05, True, True, 0.891),
    ("zen-fable5", "opencode_zen", "api_paid_frontier", 4, 60.00, 0.98, 0.88, -0.10, True, True, 0.900),
    ("zen-opus5", "opencode_zen", "api_paid_frontier", 4, None, 0.99, 0.90, -0.05, True, True, 0.928),
    ("or-frontier", "openrouter", "api_paid_frontier", 4, None, 0.95, 0.85, -0.10, True, True, 0.870),
]


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_reality(bench: float, claim: float, offset: float) -> float:
    """r(m) = clip[0,1](alpha*bench + (1-alpha)*claim + beta*offset) --
    docs/algorithm-phase1.md's Reality section, alpha=0.55, beta=0.25.
    Extracted so tests can exercise the exact formula this generator uses,
    independent of the ROWS transcription table itself.

    Read literally, "alpha*bench + (1-alpha)*claim + beta*offset" looks like
    three weights on a convex combination -- but alpha + (1-alpha) + beta =
    1.25, not 1. What's actually happening: bench and claim ARE a genuine
    convex combination (their two coefficients do sum to 1), and offset is
    a separate, bounded (+/-0.25 at beta=0.25) correction layered on top of
    that combination, before the final clip[0,1] does the rest of the work.
    docs/algorithm-phase1.md's own worked example already shows this in
    practice (bench 0.80, claim 0.95, offset -0.4 -> r = 0.7675, not 0.95),
    it's just not spelled out in the symbolic form. Not changed here: this
    is the frozen (2026-08-27) formula, reproduced exactly as specified --
    renormalizing alpha/beta to make the "weights" framing literally true
    would change every reality score in the matrix, which would change
    which model wins ties and re-derive every existing training label, and
    that is a calibration decision for a human to sign off on, not a
    documentation fix. This comment exists so nobody has to reverse-engineer
    the layering from the clip boundary again.
    """
    return clip01(ALPHA * bench + (1.0 - ALPHA) * claim + BETA * offset)


def verify(rows: list[tuple]) -> list[tuple[str, float, float]]:
    """Recompute reality for every row and return (id, computed, expected)
    for any mismatch. Empty list == every row's precomputed 11th field
    matches what compute_reality() actually derives from fields 6/7/8
    (claim, bench, offset). Pulled out of main() so pytest can call this
    without touching the filesystem.
    """
    mismatches = []
    for mid, _vendor, _lane, _floor, _cost, claim, bench, offset, _tools, _vision, expected in rows:
        reality = round(compute_reality(bench, claim, offset), 3)
        if reality != expected:
            mismatches.append((mid, reality, expected))
    return mismatches


def main() -> None:
    ids = [r[0] for r in ROWS]
    assert len(ids) == len(set(ids)), f"duplicate ids: {[i for i in ids if ids.count(i) > 1]}"
    unknown_evidence_ids = set(EVIDENCE) - set(ids)
    assert not unknown_evidence_ids, f"EVIDENCE has ids not present in ROWS: {unknown_evidence_ids}"

    mismatches = verify(ROWS)

    vendors: dict[str, list[dict]] = {}
    for mid, vendor, lane, floor, cost, claim, bench, offset, tools, vision, expected in ROWS:
        item = {
            "id": mid,
            "lane": lane,
            "ability_floor": floor,
            "vendor_claim": claim,
            "bench": bench,
            "community_offset": offset,
            "tools": tools,
            "vision": vision,
        }
        if cost is not None:
            item["in_usd_per_m"] = round(cost, 2)
        if mid in EVIDENCE:
            assert offset != 0.0, f"{mid}: has EVIDENCE entry but offset is 0 -- remove it, nothing to justify"
            item["offset_evidence"] = EVIDENCE[mid]
        vendors.setdefault(vendor, {"models": []})["models"].append(item)

    if mismatches:
        print("REALITY MISMATCHES (transcription errors) — fix before shipping:")
        for mid, got, want in mismatches:
            print(f"  {mid}: computed {got}, table says {want}")
        raise SystemExit(1)

    print(f"OK: {len(ROWS)} rows across {len(vendors)} vendors, all reality scores verified against the frozen table.")

    doc = {
        "version": "exploded-1.0",
        "frozen_at": "2026-08-27",
        "note": (
            "Transcribed and reality-verified from docs/matrix-phase1-by-lane.md "
            "by scripts/routing_data/_build_exploded_matrix.py. Prices are combined "
            "in+out $/M tokens from the source table (it doesn't break out the two "
            "directions separately) recorded here as in_usd_per_m with out_usd_per_m "
            "omitted; unit_cost() sums both, so the total is correct even though the "
            "in/out split isn't independently known. Models with '—' (no published "
            "price) omit both price fields so unit_cost() falls back to its 9999 "
            "sentinel rather than being treated as free."
        ),
        "alpha": ALPHA,
        "beta": BETA,
        "confidence_tau": CONFIDENCE_TAU,
        "lane_order": LANE_ORDER,
        "vendors": vendors,
    }

    out_path = "config/matrix.exploded.v1.yaml"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("# AUTO-GENERATED from docs/matrix-phase1-by-lane.md — see\n")
        fh.write("# scripts/routing_data/_build_exploded_matrix.py for provenance and\n")
        fh.write("# the reality-score verification that ran before this file was written.\n")
        fh.write("# Do not hand-edit; regenerate via that script if the source table changes.\n")
        yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True, width=100)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
