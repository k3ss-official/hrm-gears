#!/usr/bin/env python3
"""Build a Twin-T4 harvest pack: replayable bundle, not a pet VM.

Writes var/kaggle-pack/<run_id>/ with MANIFEST.json, a slim source tree,
kernel-metadata.json, and the session notebook. Weights stay out unless
--include-sudoku-ckpt. Kaggle fetches published checkpoints over the Hub.

This is the pack step. It does not train a routing head.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK_PARENT = ROOT / "var" / "kaggle-pack"

COPY_DIRS = (
    "hrm_gears",
    "models",
    "scripts",
    "config",
    "utils",
    "docs",
)
COPY_FILES = (
    "requirements.txt",
    "pyproject.toml",
    "LICENSE",
    "NOTICE",
    "pretrain.py",
    "evaluate.py",
    "puzzle_dataset.py",
)
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "var",
    "wandb",
    "raw-data",
    "checkpoints",
}


def git_describe(root: Path) -> dict[str, str | bool]:
    def run(args: list[str]) -> str:
        return subprocess.check_output(args, cwd=root, text=True).strip()

    sha = run(["git", "rev-parse", "HEAD"])
    dirty = bool(run(["git", "status", "--porcelain"]))
    try:
        subject = run(["git", "log", "-1", "--format=%s"])
    except subprocess.CalledProcessError:
        subject = ""
    return {"sha": sha, "dirty": dirty, "subject": subject}


def copy_tree(src: Path, dest: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        skipped = {n for n in names if n in SKIP_DIR_NAMES or n.endswith(".pyc")}
        return skipped

    shutil.copytree(src, dest, ignore=ignore, dirs_exist_ok=True)


def write_kernel_metadata(dest: Path, username: str, slug: str) -> None:
    payload = {
        "id": f"{username}/{slug}",
        "title": "hrm-gears Twin-T4 harvest",
        "code_file": "twin_t4.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "keywords": ["gpu", "pytorch", "hrm"],
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": [],
        "model_sources": [],
    }
    (dest / "kernel-metadata.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Pack directory (default: var/kaggle-pack/<utc>-<sha7>)",
    )
    parser.add_argument(
        "--include-sudoku-ckpt",
        action="store_true",
        help="Copy the ~104 MiB Sudoku checkpoint into the pack (optional).",
    )
    parser.add_argument(
        "--kernel-slug",
        default="hrm-gears-twin-t4",
        help="Kaggle kernel slug (default: hrm-gears-twin-t4)",
    )
    args = parser.parse_args()

    git = git_describe(ROOT)
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{utc}-{git['sha'][:7]}"
    dest = args.out or (PACK_PARENT / run_id)
    if dest.exists():
        print(f"refusing to overwrite existing pack: {dest}", file=sys.stderr)
        return 2
    dest.mkdir(parents=True)
    tree = dest / "tree"
    tree.mkdir()

    for name in COPY_DIRS:
        src = ROOT / name
        if src.is_dir():
            copy_tree(src, tree / name)
    for name in COPY_FILES:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, tree / name)

    notebook_src = ROOT / "scripts" / "kaggle" / "twin_t4.ipynb"
    shutil.copy2(notebook_src, dest / "twin_t4.ipynb")

    ckpt_included = False
    sudoku = ROOT / "checkpoints" / "sudoku-extreme"
    if args.include_sudoku_ckpt:
        if not (sudoku / "checkpoint").is_file():
            print("Sudoku checkpoint missing; run scripts/fetch_checkpoints.py", file=sys.stderr)
            return 1
        copy_tree(sudoku, tree / "checkpoints" / "sudoku-extreme")
        ckpt_included = True

    username = os.environ.get("KAGGLE_USERNAME", "REPLACE_ME")
    write_kernel_metadata(dest, username, args.kernel_slug)

    manifest = {
        "schema_version": "1",
        "run_id": run_id,
        "purpose": "twin-t4-harvest-pack",
        "stage": "smoke",
        "stage2_routing_training": False,
        "git": git,
        "packed_utc": utc,
        "include_sudoku_ckpt": ckpt_included,
        "kernel_slug": args.kernel_slug,
        "kaggle_username_placeholder": username == "REPLACE_ME",
        "accelerator_required": "GPU T4 x2",
        "hardware": "2x NVIDIA Tesla T4",
        "public_repo": "https://github.com/k3ss-official/hrm-gears",
    }
    (dest / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copy2(dest / "MANIFEST.json", tree / "PACK_MANIFEST.json")

    print(f"run_id: {run_id}")
    print(f"pack: {dest}")
    print(f"git_sha: {git['sha']}{' (dirty)' if git['dirty'] else ''}")
    print(f"sudoku_ckpt: {ckpt_included}")
    print("next: docs/compute.md — Twin-T4 harvest, 9 steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
