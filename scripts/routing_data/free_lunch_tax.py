#!/usr/bin/env python3
"""Free-lunch tax — whitepaper v0.2, the section between "3. Objects" and
"5. Need" (page 3 of docs/HRM-GEARS-working-paper-v0.2.pdf; the PDF's own
section numbering skips from 3 to 5 there, so it is cited here as "§4").

STATUS: SPECIFIED BUT NOT WIRED IN. On purpose. Read this before wiring it
into `policy_nested.py.choose()` or adding real fields to
`config/matrix.exploded.v1.yaml`.

The frozen algorithm spec (`docs/algorithm-phase1.md`, "Frozen: 2026-08-27")
does not mention a free-lunch tax anywhere in its I -> T -> E definition —
the "Then" step there reads only "cheapest model in that lane by unit cost."
The frozen matrix (`config/matrix.exploded.v1.yaml`, `frozen_at: 2026-08-27`)
has no free_motive / throttle_class / priority_class fields. This is not an
oversight: the working paper says so itself, twice —

    "v0.2 matrix work: add free_motive, throttle_class, priority_class.
     Not yet on the 2026-08-27 YAML." (§4)

    "Free-lunch columns specified, not yet on the frozen YAML." (§13,
     Status as of this draft)

The paper gives the formula and two directional constraints on kappa, but
does NOT give numeric weights:

    tau_f(m) = clip[0,1](theta_motive + theta_throttle + theta_priority)
    p-effective = p + kappa * tau_f

    "kappa is large enough that a throttled $0 SKU can lose to a cheap
     metered SKU when tags say medium+ ... On shallow/none/low, tau_f may
     still lose to $0 -- that is the point of having a lunch at all."

Four qualitative motive categories are named (arena entry, loss-leader
catalogue, subscription fill, open-weights flex) with prose about what each
"usually means" -- but no numbers are attached to any of them, and no
throttle_class / priority_class taxonomy is given at all beyond the two
sentences quoted above.

Wiring invented numbers into the frozen chooser and frozen matrix would mean
silently unfreezing two already-frozen artifacts on my own authority, using
weights that exist nowhere in the source material -- exactly the kind of
gap-filling the overnight brief said not to do ("accept nothing short of
pure gold signal"). So this module implements the *mechanism* exactly as
specified, as a pure function of caller-supplied theta/kappa values, fully
tested (see tests/test_free_lunch_tax.py) against the paper's own two
directional constraints -- so the day real theta/kappa values are supplied
(a product/business calibration decision, not an engineering one), there is
a tested harness ready to receive them and a known-satisfiable target to
calibrate against. Until then it is dead code, imported by nothing else in
the package, which is the honest state for a feature whose own spec says
"not yet."
"""

from __future__ import annotations

from dataclasses import dataclass


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class FreeLunchInputs:
    """Per-model inputs to the tax, as named in the whitepaper.

    theta_motive: penalty for *why* the SKU is priced at $0 (arena entry /
        loss-leader catalogue / subscription fill / open-weights flex --
        the paper names these four categories but gives no numeric mapping).
    theta_throttle: penalty for observed or expected rate-limiting relative
        to the paid tier of the same vendor.
    theta_priority: penalty for lower scheduler priority when the vendor's
        paid traffic is busy.

    All three are caller-supplied, 0..1-ish per the paper's own worked
    example shape (it clips their sum to [0,1] the same way `reality()`
    clips its own three-term sum) -- this module takes no position on what
    real values should be for any real vendor.
    """

    theta_motive: float
    theta_throttle: float
    theta_priority: float


def tau_f(inputs: FreeLunchInputs) -> float:
    """tau_f(m) = clip[0,1](theta_motive + theta_throttle + theta_priority)."""
    return clip01(inputs.theta_motive + inputs.theta_throttle + inputs.theta_priority)


def effective_cost(p: float, inputs: FreeLunchInputs, kappa: float) -> float:
    """p-effective = p + kappa * tau_f(m).

    `kappa` is not specified numerically by the paper either -- only the
    directional constraint that it must be "large enough that a throttled
    $0 SKU can lose to a cheap metered SKU when tags say medium+", while
    still letting tau_f "lose to $0" on shallow/none/low. Caller-supplied,
    same as the theta terms.
    """
    return p + kappa * tau_f(inputs)
