#!/usr/bin/env python3
"""Schema + invariant + evidence-citation gate for config/matrix.exploded.v1.yaml.

    python scripts/routing_data/validate_exploded_matrix.py
    python scripts/routing_data/validate_exploded_matrix.py --strict

Companion to validate.py, which gates the flat-matrix (config/model_matrix.v1.yaml)
JSONL drop. This one gates the exploded 48-model matrix directly -- nothing
else in the repo checked its shape before tonight.

Evidence-citation gate (architecture-decision-v2.md §6.6): every model whose
community_offset is nonzero is making a claim ("this vendor's bench/claim
numbers are over- or under-stated by this much") with no evidence trail
today. That's exactly as unfalsifiable as the vendor claims the offset
exists to correct for. This validator requires a non-empty `offset_evidence`
string field (a URL, a dated community report, an internal test log) on any
model with a nonzero offset. It is a NEW, additive, optional schema field --
adding it does not change unit_cost(), reality(), or any chooser behavior,
so running this validator is safe against the frozen matrix as-is.

It will currently report most of the 48 models as failing this gate, because
none of them have offset_evidence yet. That is accurate, not a bug in the
validator: the citations have to come from whoever set each offset (only
they know what community chatter or test run justified -0.15 for
nous-longcat-2, for instance) -- inventing plausible-sounding citations here
would be fabrication, not a fix. Run with --strict to see the real count and
which ids need backfilling; the default (non-strict) mode reports the same
information but exits 0, so this can be run informationally without turning
red on a legitimate, already-known, not-yet-actioned gap.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _build_exploded_matrix import compute_reality  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "config" / "matrix.exploded.v1.yaml"

REQUIRED_MODEL_FIELDS = {
    "id",
    "lane",
    "ability_floor",
    "vendor_claim",
    "bench",
    "community_offset",
    "tools",
    "vision",
}
VALID_ABILITY_FLOORS = {1, 2, 3, 4}


def load_raw(path: Path = MATRIX_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(raw: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    evidence_missing: list[str] = []
    seen_ids: set[str] = set()
    n_models = 0
    n_nonzero_offset = 0

    for key in ("alpha", "beta", "confidence_tau", "lane_order", "vendors"):
        if key not in raw:
            errors.append(f"top-level: missing {key!r}")
    lane_order = set(raw.get("lane_order") or [])

    for vendor, block in (raw.get("vendors") or {}).items():
        for item in block.get("models") or []:
            n_models += 1
            mid = item.get("id", f"<unnamed in {vendor}>")
            missing = REQUIRED_MODEL_FIELDS - set(item)
            if missing:
                errors.append(f"{mid}: missing fields {sorted(missing)}")
                continue
            if mid in seen_ids:
                errors.append(f"{mid}: duplicate id")
            seen_ids.add(mid)
            if item["ability_floor"] not in VALID_ABILITY_FLOORS:
                errors.append(f"{mid}: ability_floor {item['ability_floor']!r} not in {VALID_ABILITY_FLOORS}")
            if item["lane"] not in lane_order:
                errors.append(f"{mid}: lane {item['lane']!r} not in lane_order {sorted(lane_order)}")
            for field in ("vendor_claim", "bench"):
                v = item[field]
                if not isinstance(v, (int, float)) or not 0.0 <= float(v) <= 1.0:
                    errors.append(f"{mid}: {field}={v!r} not in [0,1]")
            offset = item["community_offset"]
            if not isinstance(offset, (int, float)) or not -1.0 <= float(offset) <= 1.0:
                errors.append(f"{mid}: community_offset={offset!r} not in [-1,1]")
            if offset != 0:
                n_nonzero_offset += 1
                evidence = item.get("offset_evidence")
                if not evidence or not str(evidence).strip():
                    evidence_missing.append(mid)
            reality = compute_reality(float(item["bench"]), float(item["vendor_claim"]), float(offset))
            if not 0.0 <= reality <= 1.0:
                errors.append(f"{mid}: recomputed reality {reality!r} out of [0,1] (clip should prevent this)")

    return {
        "n_models": n_models,
        "n_nonzero_offset": n_nonzero_offset,
        "n_evidence_missing": len(evidence_missing),
        "evidence_missing_ids": evidence_missing,
        "schema_errors": errors,
        "schema_pass": not errors,
        "evidence_pass": not evidence_missing,
        "pass": not errors and not evidence_missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=MATRIX_PATH)
    parser.add_argument("--strict", action="store_true", help="exit 1 if the evidence-citation gate fails too")
    args = parser.parse_args()

    raw = load_raw(args.path)
    result = validate(raw)
    print(json.dumps(result, indent=2))

    if result["schema_errors"]:
        return 1
    if args.strict and not result["evidence_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
