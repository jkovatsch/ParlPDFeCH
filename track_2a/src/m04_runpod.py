# SPDX-License-Identifier: Apache-2.0
"""Runpod pod for the GPU training of the isolation readout (step 3.9): create, show, delete.

The Runpod API key comes from the environment variable RUNPOD_API_KEY, else from the file
`.env.runpod` in the project folder track_2a (mode 600; `.env*` is in .gitignore and .dockerignore).
The script never prints it. SSH: the environment variable RUNPOD_SSH_KEY gives the private key file
(default ~/.ssh/runpod_parlpdfech); use a key pair only for this project, for example
`ssh-keygen -t ed25519 -f ~/.ssh/runpod_parlpdfech`. The public half (<key file>.pub) goes to the pod
as the environment variable PUBLIC_KEY, not into the Runpod account. The command create stops if
the public half does not exist.

Data centers: the create request permits only data centers in Europe (EU_DATA_CENTERS). The script
does not examine the region after the creation.

Costs: the script has no automatic removal of a pod. The operator deletes the pod after each job
(command delete).

Usage:
  python3 src/m04_runpod.py create [--gpu "NVIDIA H100 80GB HBM3"] [--disk 80]
  python3 src/m04_runpod.py show POD_ID
  python3 src/m04_runpod.py ssh POD_ID          (prints the ssh command)
  python3 src/m04_runpod.py delete POD_ID
  python3 src/m04_runpod.py list
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://rest.runpod.io/v1"
SSH_KEY = Path(os.environ.get("RUNPOD_SSH_KEY") or Path.home() / ".ssh/runpod_parlpdfech").expanduser()
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
EU_DATA_CENTERS = ["EU-RO-1", "EU-SE-1", "EU-NL-1", "EU-CZ-1", "EU-FR-1", "EUR-IS-1", "EUR-IS-2", "EUR-IS-3", "EUR-NO-1"]
GPUS = ["NVIDIA H100 80GB HBM3", "NVIDIA H100 NVL", "NVIDIA H100 PCIe", "NVIDIA A100-SXM4-80GB", "NVIDIA A100 80GB PCIe"]


def key() -> str:
    if os.environ.get("RUNPOD_API_KEY"):
        return os.environ["RUNPOD_API_KEY"].strip()
    env = ROOT / ".env.runpod"
    for line in (env.read_text().splitlines() if env.exists() else []):
        if line.startswith("RUNPOD_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("no RUNPOD_API_KEY in the environment or in .env.runpod")


def call(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json",
                                          "User-Agent": "parlpdfech/1.0 (curl-compatible)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]


def summary(p: dict) -> dict:
    keep = ("id", "name", "desiredStatus", "costPerHr", "adjustedCostPerHr", "gpuCount", "publicIp", "portMappings",
            "imageName", "containerDiskInGb", "lastStatusChange", "uptimeSeconds")
    out = {k: p.get(k) for k in keep if k in p}
    m = p.get("machine") or {}
    out["gpu"] = m.get("gpuTypeId") or (p.get("gpu") or {}).get("id")
    out["dataCenter"] = m.get("dataCenterId") or p.get("dataCenterId")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["create", "show", "ssh", "delete", "list"])
    ap.add_argument("pod", nargs="?")
    ap.add_argument("--gpu", default=None)
    ap.add_argument("--disk", type=int, default=80)
    args = ap.parse_args()
    if args.cmd == "list":
        st, res = call("GET", "/pods")
        print(st, json.dumps([summary(p) for p in res] if isinstance(res, list) else res, indent=1))
    elif args.cmd == "create":
        pub_file = SSH_KEY.with_name(SSH_KEY.name + ".pub")
        if not pub_file.exists():
            sys.exit(f"no public key {pub_file}: make a key pair only for this project "
                     f"(ssh-keygen -t ed25519 -f {SSH_KEY}) or set RUNPOD_SSH_KEY")
        pub = pub_file.read_text().strip()
        body = {"name": "parlpdfech-iso", "imageName": IMAGE, "gpuTypeIds": [args.gpu] if args.gpu else GPUS,
                "gpuCount": 1, "cloudType": "SECURE", "containerDiskInGb": args.disk, "volumeInGb": 0,
                "ports": ["22/tcp"], "supportPublicIp": True, "env": {"PUBLIC_KEY": pub},
                "dataCenterIds": EU_DATA_CENTERS}
        st, res = call("POST", "/pods", body)
        print(st, json.dumps(summary(res) if isinstance(res, dict) else res, indent=1))
    elif args.cmd == "show":
        st, res = call("GET", f"/pods/{args.pod}")
        print(st, json.dumps(summary(res) if isinstance(res, dict) else res, indent=1))
    elif args.cmd == "ssh":
        st, res = call("GET", f"/pods/{args.pod}")
        ip, ports = res.get("publicIp"), res.get("portMappings") or {}
        port = ports.get("22") if isinstance(ports, dict) else None
        print(f"ssh -i {SSH_KEY} -o StrictHostKeyChecking=accept-new -p {port} root@{ip}")
    elif args.cmd == "delete":
        st, res = call("DELETE", f"/pods/{args.pod}")
        print(st, res)


if __name__ == "__main__":
    main()
