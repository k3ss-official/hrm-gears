# References and thanks

This project sits on other people's work. That is the point.

## Hermes / why this repo exists

Nous Research — [Hermes](https://nousresearch.com), the agent harness this
router is being built to serve first. The routing contract is a matrix plus
a model id; any harness that can honour that can consume the same unit.

[@Teknium](https://x.com/Teknium1) (Andy Keh) — hat tip. Hermes, OpenHermes,
and the culture of actually shipping local agents are the reason this is
not another abstract router paper.

[@tonysimmons_](https://x.com/tonysimmons_) — for kicking the project from
talk into a tree on disk.

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

## Surveyed, not chosen as the router

Inception Labs (Khanna, Kharbanda, Li, Varma, Wang, et al.).
**Mercury: Ultra-Fast Language Models Based on Diffusion.**
arXiv:2506.17298, 2025.
<https://arxiv.org/abs/2506.17298>
<https://www.inceptionlabs.ai/>

Mercury / Mercury 2 is a diffusion LLM: non-autoregressive generation,
Transformer-parameterised denoiser. Looked at as a non-standard LM.
Rejected as the *router* because it still generates language; the job
here is allotment. It remains a candidate **gear** in the matrix.

Tiny Recursive Models (TRM) — recursive refinement in the same
neighbourhood as HRM. Noted, not the unit in this tree.

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
- Kaggle Notebooks — **GPU T4 x2** (2 × NVIDIA Tesla T4) for Twin-T4 harvest.
  Free GPU time is a **weekly** quota (historically ~30 h/week), with
  per-session caps. Not a dedicated box. See [compute.md](compute.md).

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
