"""Inference-only stand-in for `flash_attn.flash_attn_func`.

Upstream HRM (`models/layers.py`) imports FlashAttention 3, then 2:

    from flash_attn_interface import flash_attn_func
    from flash_attn import flash_attn_func          # fallback

Those packages are CUDA extensions (Dao et al., FlashAttention 2022;
FlashAttention-2 2023; Hopper FA3). They do not build on Apple Silicon.

Layout contract — identical to FlashAttention's Python API used here:

    q, k, v : [batch, seq, heads, head_dim]
    returns : [batch, seq, heads, head_dim]

We permute to the SDPA layout [batch, heads, seq, dim], call
`torch.nn.functional.scaled_dot_product_attention`, and permute back.

This is *not* bit-identical to FA2/FA3. Softmax is the same operation;
tiling, dropout fused kernels, and I/O-aware scheduling are not. Use
this shim for load/forward smoke tests and Apple-Silicon research. Do
not quote FA2/FA3 latency or memory numbers from runs that used it.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def flash_attn_func(q, k, v, causal: bool = False, **kwargs):
    """SDPA with the FlashAttention q/k/v layout HRM expects."""
    del kwargs  # FA2/FA3 extra flags are ignored on purpose
    query = q.transpose(1, 2)
    key = k.transpose(1, 2)
    value = v.transpose(1, 2)
    out = F.scaled_dot_product_attention(query, key, value, is_causal=causal)
    return out.transpose(1, 2).contiguous()
