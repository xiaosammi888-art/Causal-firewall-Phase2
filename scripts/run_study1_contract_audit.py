#!/usr/bin/env python3
"""Compile and audit all five frozen Study 1 batches without API access."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from causal_firewall.study1_confirmatory_runner import run_confirmatory_offline_runner


def main() -> int:
    output_root = ROOT / "reproduction_outputs/contract_audit"
    policy = ROOT / "experiments/study1/access_policy.json"
    totals = {"contracts": 0, "arm_packets": 0, "request_templates": 0, "gates": 0}
    for batch in range(1, 6):
        manifest = ROOT / f"experiments/study1/confirmatory_frozen_batch{batch:02d}/freeze_manifest.json"
        output = run_confirmatory_offline_runner(ROOT, manifest, policy, output_root / f"batch{batch:02d}")
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        if summary["status"] != "offline_test_pass" or summary["network_calls"] != 0 or summary["model_called"]:
            raise ValueError(f"offline batch audit failed: {batch:02d}")
        totals["contracts"] += summary["contracts"]
        totals["arm_packets"] += summary["arm_packets"]
        totals["request_templates"] += summary["request_templates"]
        totals["gates"] += summary["gates_passed"]
    if totals["contracts"] != 40 or totals["request_templates"] != 528:
        raise ValueError(f"unexpected compiled totals: {totals}")
    print(json.dumps({"offline_contract_audit": "pass", **totals}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
