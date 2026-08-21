# Optional CUDA one-shot replay. Not the M4 install path.
# M4 bring-up stays: ./scripts/bootstrap_env.sh
# This image is for a machine that already has an NVIDIA GPU.
#
#   docker build -f scripts/kaggle/Dockerfile -t hrm-gears-twin-t4 .
#   docker run --gpus all --rm -v "$PWD/var/kaggle-harvest/local:/out" hrm-gears-twin-t4
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
WORKDIR /work
COPY . /work
RUN python -m pip install -q huggingface_hub omegaconf pyyaml einops
ENV HARVEST_OUT=/out
CMD ["python", "scripts/kaggle/run_session.py", "--out", "/out"]
