#!/usr/bin/env python3
"""Download official Sapient HRM checkpoints (not redistributed)."""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
REPOS = {
    "sudoku-extreme": "sapientinc/HRM-checkpoint-sudoku-extreme",
    "maze-30x30-hard": "sapientinc/HRM-checkpoint-maze-30x30-hard",
    "ARC-2": "sapientinc/HRM-checkpoint-ARC-2",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(REPOS),
        metavar="NAME",
        help="Fetch this subset (default: all three).",
    )
    args = parser.parse_args()
    selected = {name: REPOS[name] for name in args.only} if args.only else REPOS

    dest_root = ROOT / "checkpoints"
    dest_root.mkdir(exist_ok=True)
    named = dest_root / "sapientinc"
    named.mkdir(exist_ok=True)
    for short, repo in selected.items():
        local = dest_root / short
        print(f"fetch {repo} -> {local}")
        snapshot_download(repo_id=repo, local_dir=str(local))
        link = named / f"HRM-checkpoint-{short}"
        if not link.exists():
            link.symlink_to(Path("..") / short)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
