#!/usr/bin/env python3
"""Pull Twin-T4 artifacts off Kaggle and check the harvest MANIFEST.

Requires the Kaggle CLI and an API token at ~/.kaggle/kaggle.json
(create one at https://www.kaggle.com/settings — never commit it).

    python scripts/kaggle/harvest.py --kernel $KAGGLE_USERNAME/hrm-gears-twin-t4

Stops short of deleting the remote notebook. Teardown is: stop the
Kaggle session in the UI so the VM dies. See docs/compute.md.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARVEST_PARENT = ROOT / "var" / "kaggle-harvest"
REQUIRED = ("MANIFEST.json", "smoke.json", "session.log")


def kaggle_bin() -> str:
    found = shutil.which("kaggle")
    if found:
        return found
    print(
        "BLOCKED: kaggle CLI not on PATH.\n"
        "  pip install kaggle\n"
        "  put API token at ~/.kaggle/kaggle.json (from https://www.kaggle.com/settings)",
        file=sys.stderr,
    )
    sys.exit(4)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kernel",
        required=True,
        help="Kaggle kernel id: <username>/hrm-gears-twin-t4",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Destination directory (default: var/kaggle-harvest/<utc>-<slug>)",
    )
    args = parser.parse_args()

    token = Path.home() / ".kaggle" / "kaggle.json"
    if not token.is_file():
        print(
            "BLOCKED: ~/.kaggle/kaggle.json missing.\n"
            "  Create an API token at https://www.kaggle.com/settings",
            file=sys.stderr,
        )
        return 4

    slug = args.kernel.replace("/", "-")
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = args.out or (HARVEST_PARENT / f"{utc}-{slug}")
    dest.mkdir(parents=True)

    cmd = [kaggle_bin(), "kernels", "output", args.kernel, "-p", str(dest)]
    print(" ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        print(f"BLOCKED: kaggle kernels output failed ({exc.returncode})", file=sys.stderr)
        return exc.returncode or 1

    harvest = dest / "harvest"
    if not harvest.is_dir():
        # Kaggle sometimes flattens /kaggle/working into the download root.
        if (dest / "MANIFEST.json").is_file():
            harvest = dest
        else:
            print(f"BLOCKED: no harvest/ under {dest}", file=sys.stderr)
            return 1

    missing = [name for name in REQUIRED if not (harvest / name).is_file()]
    if missing:
        print(f"BLOCKED: harvest missing {missing}", file=sys.stderr)
        return 1

    manifest = json.loads((harvest / "MANIFEST.json").read_text(encoding="utf-8"))
    smoke = json.loads((harvest / "smoke.json").read_text(encoding="utf-8"))
    print(f"harvest: {harvest}")
    print(f"device_used: {manifest.get('device_used')}")
    print(f"device_count: {manifest.get('device_count')}")
    print(f"t4_x2_seen: {manifest.get('t4_x2_seen')}")
    print(f"stage2_routing_training: {manifest.get('stage2_routing_training')}")
    print(f"first_q_halt_gt: {smoke.get('first_q_halt_gt_q_continue_step')}")
    print(f"latency_s: {smoke.get('latency_s')}")
    print("teardown: Kaggle → this notebook → Stop session. Confirm nothing running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
