# References and thanks

This project sits on other people's work. That is the point.

## Primary — Hierarchical Reasoning Model

Guan Wang, Jin Li, Yuhao Sun, Xing Chen, Changling Liu, Yue Wu, Meng Lu,
Sen Song, and Yasin Abbasi Yadkori.
**Hierarchical Reasoning Model.**
arXiv:2506.21734, 2025.
<https://arxiv.org/abs/2506.21734>

Code (Apache License 2.0):
<https://github.com/sapientinc/HRM>

Checkpoints (used, not redistributed):
<https://huggingface.co/sapientinc/HRM-checkpoint-sudoku-extreme>
<https://huggingface.co/sapientinc/HRM-checkpoint-maze-30x30-hard>
<https://huggingface.co/sapientinc/HRM-checkpoint-ARC-2>

Thank you to the Sapient Intelligence authors and contributors for
releasing a 27M non-Transformer reasoner with weights, data builders, and
an honest training recipe. hrm-gear is an adaptation layer, not a
re-implementation and not a claim of authorship.

The original project README is preserved at
[upstream/HRM.README.md](upstream/HRM.README.md).

## Adaptive Computation Time

Alex Graves.
**Adaptive Computation Time for Recurrent Neural Networks.**
arXiv:1603.08983, 2016.
<https://arxiv.org/abs/1603.08983>

HRM's halt/continue Q-head is an ACT-style wrapper. Graves is the
reference for the idea that a recurrent net should learn *how many*
inner steps to take.

## Attention kernels

Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra, and Christopher Ré.
**FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness.**
NeurIPS, 2022.

Tri Dao.
**FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning.**
2023.

Upstream training depends on these CUDA extensions. This repository
substitutes PyTorch SDPA on Apple Silicon and does not vendor their code.

## Puzzle benchmarks used by upstream data builders

François Chollet.
**On the Measure of Intelligence.**
arXiv:1911.01547, 2019. (ARC)

ARC-AGI / ARC-AGI-2 datasets (submodules in `.gitmodules`):
<https://github.com/fchollet/ARC-AGI>
<https://github.com/arcprize/ARC-AGI-2>

ConceptARC:
<https://github.com/victorvikram/ConceptARC>

Sudoku-Extreme and Maze-30x30-Hard source CSVs live on Hugging Face under
`sapientinc/` and are fetched by the upstream dataset scripts.

## Software

- PyTorch (Meta / community) — runtime and SDPA.
- Hugging Face Hub — checkpoint transport.
- Hydra / OmegaConf — upstream experiment config.
- wandb — upstream training logs (optional here).

## Related routing literature (context only)

These are not dependencies. They are the Transformer-side state of the
art we are *not* copying:

- Ong et al., RouteLLM.
- Chen et al., FrugalGPT.
- NVIDIA NeMo / cascade routers.

A 27M hierarchical recurrent router is a different bet: local, cheap,
sample-efficient, no CoT in the decision path.

## License posture

Original HRM source remains Apache-2.0. Our additions are Apache-2.0.
See `LICENSE` and `NOTICE`. Do not drop the Apache header from modified
upstream files. We have not modified `models/` in this tree; compatibility
is injected via `PYTHONPATH` / a `.pth` file.
