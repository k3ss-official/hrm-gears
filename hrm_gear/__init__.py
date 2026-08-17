"""hrm-gear: adapt Sapient HRM into a local model-routing brain.

The 27M Hierarchical Reasoning Model is not a Transformer. This package
does not reimplement it. It loads the published weights, runs ACT on
devices without CUDA FlashAttention, and records the measurements that
decide whether the architecture is a viable discrete router.
"""

from .runtime import (
    load_hrm,
    move_carry,
    pick_device,
    run_act,
    strip_state_dict,
)

__all__ = [
    "load_hrm",
    "move_carry",
    "pick_device",
    "run_act",
    "strip_state_dict",
]
