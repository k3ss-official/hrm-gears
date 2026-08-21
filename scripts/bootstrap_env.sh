#!/usr/bin/env bash
# Bootstrap the Apple-Silicon inference environment for hrm-gears.
#
# Upstream HRM (Wang et al., 2025) requires CUDA 12.x + FlashAttention.
# This script does *not* install those. It installs PyTorch MPS, the
# published Python deps, and a site .pth so `import flash_attn` resolves
# to hrm_gears.compat.flash_attn (SDPA).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-/opt/homebrew/Caskroom/miniforge/base/bin/python3.12}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3.12 || command -v python3)"
fi

if [[ ! -d .venv ]]; then
  "$PYTHON" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install torch
python -m pip install -r requirements.txt
python -m pip install numpy

SITE="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "${ROOT}/hrm_gears/compat" > "${SITE}/hrm_gears_flash_attn.pth"

python - <<'PY'
import flash_attn
import torch
from models.hrm.hrm_act_v1 import HierarchicalReasoningModel_ACTV1
print("python", __import__("sys").version.split()[0])
print("torch", torch.__version__, "mps", torch.backends.mps.is_available())
print("flash_attn", flash_attn.__file__)
print("HRM class", HierarchicalReasoningModel_ACTV1.__name__)
PY

echo "bootstrap ok"
echo "download checkpoints with:  python scripts/fetch_checkpoints.py"
