# Door 3 — CPU install / smoke. Runs ./setup unchanged.
# Not Twin-T4 harvest. GPU path: scripts/kaggle + docs/compute.md
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY . /work
RUN chmod +x setup scripts/setup scripts/bootstrap_env.sh \
    && rm -rf .venv

# Checkpoints are fetched at run time (gitignored, not baked).
CMD ["./setup"]
