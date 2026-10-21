#!/usr/bin/env python3
"""Validate and audit a new experiment without credentials or network access."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from causal_firewall.architectures import FirewallArchitecture, ManualWhitelistArchitecture
from causal_firewall.io import load_policy
from causal_firewall.models import BuildContext
from causal_firewall.providers import OpenAIResponsesDryRunAdapter, validate_stateless_request
from causal_firewall.study1_contract import load_contract
from causal_firewall.study1_prefreeze import (
    build_source_matched_persona,
    study1_clean_fields,
    study1_cue_field,
)


DEFAULT_EXAMPLE = ROOT / "examples/new_experiment_template/completed_example/experiment_contract.json"
DEFAULT_POLICY = ROOT / "examples/new_experiment_template/access_policy.template.json"
DEFAULT_OUTPUT = ROOT / "reproduction_outputs/new_experiment_example"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a new experiment through C and D without calling a model."
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_EXAMPLE)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def audit(contract_path: Path, policy_path: Path, output_root: Path) -> Path:
    contract = load_contract(contract_path)
    policy = load_policy(policy_path)
    persona = build_source_matched_persona(contract, 1)
    architectures = {
        "C_fresh_context_manual_whitelist": ManualWhitelistArchitecture(contract),
        "D_labeled_causal_firewall": FirewallArchitecture(contract, policy),
    }
    adapter = OpenAIResponsesDryRunAdapter(
        model_snapshot="DRY_RUN_VERSIONED_MODEL_REQUIRED",
        temperature=None,
        max_output_tokens=256,
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = output_root / run_id
    requests = output / "requests"
    requests.mkdir(parents=True, exist_ok=False)

    rows = []
    sequence = 0
    for arm in contract["materials"]["arms"]:
        clean_fields = study1_clean_fields(contract, persona, arm)
        for cue in ("aligned", "reversed"):
            contaminated_fields = [*clean_fields, study1_cue_field(contract, cue)]
            for architecture_name, architecture in architectures.items():
                sequence += 1
                context = BuildContext(
                    participant_id=persona["participant_id"],
                    current_arm=arm,
                    session_id=f"dry-run-{sequence:03d}",
                )
                result = architecture.build(contaminated_fields, context)
                prepared = adapter.prepare(
                    result,
                    study_id=contract["identity"]["study_id"],
                    contract_version=contract["identity"]["contract_version"],
                )
                violations = validate_stateless_request(prepared)
                cue_visible = "summary_context" in result.packet
                expected_cue_visible = architecture_name.startswith("C_")
                record = {
                    "sequence": sequence,
                    "arm": arm,
                    "cue": cue,
                    "architecture": architecture_name,
                    "status": result.status,
                    "allowed_fields": list(result.allowed_fields),
                    "denied_fields": list(result.denied_fields),
                    "cue_visible": cue_visible,
                    "expected_cue_visible": expected_cue_visible,
                    "cue_gate_passed": cue_visible is expected_cue_visible,
                    "stateless_violations": violations,
                    "network_enabled": prepared.network_enabled,
                    "request_hash": prepared.request_hash,
                }
                rows.append(record)
                request_path = requests / f"{sequence:03d}_{arm}_{cue}_{architecture_name[0]}.json"
                request_path.write_text(
                    json.dumps(
                        {
                            "dry_run": True,
                            "network_calls": 0,
                            "model_called": False,
                            "audit": record,
                            "body": prepared.body,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

    gates_passed = all(
        row["status"] == "ready"
        and row["cue_gate_passed"]
        and not row["stateless_violations"]
        and row["network_enabled"] is False
        for row in rows
    )
    summary = {
        "status": "pass" if gates_passed else "fail",
        "study_id": contract["identity"]["study_id"],
        "contract_status": contract["execution"]["contract_status"],
        "arms": len(contract["materials"]["arms"]),
        "request_templates": len(rows),
        "architectures": list(architectures),
        "network_calls": 0,
        "model_called": False,
        "credentials_read": False,
        "cue_boundary": {
            "manual_whitelist_admits_summary_context": all(
                row["cue_visible"] for row in rows if row["architecture"].startswith("C_")
            ),
            "causal_firewall_denies_summary_context": all(
                not row["cue_visible"] for row in rows if row["architecture"].startswith("D_")
            ),
        },
        "rows": rows,
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if not gates_passed:
        raise RuntimeError(f"new experiment audit failed: {output}")
    return output


def main() -> int:
    arguments = parse_args()
    output = audit(arguments.contract, arguments.policy, arguments.output_root)
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    print(
        f"new_experiment_audit={summary['status']} "
        f"requests={summary['request_templates']} network_calls=0 output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
