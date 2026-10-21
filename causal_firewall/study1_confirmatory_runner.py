"""Offline-only runner compiler for frozen Study 1 confirmatory batches.

This module deliberately contains no credential loader, HTTP client, or live
execution path. It binds request templates to a frozen contract manifest and
fails closed for draft or merely dual-reviewed contracts.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .architectures import FirewallArchitecture, ManualWhitelistArchitecture
from .hashing import canonical_json, sha256_json
from .models import BuildContext
from .providers import OpenAIResponsesDryRunAdapter, validate_stateless_request
from .study1_contract import load_contract, normalized_material_hash
from .study1_prefreeze import (
    ARCHITECTURE_C,
    ARCHITECTURE_D,
    build_response_schema,
    build_source_matched_persona,
    study1_clean_fields,
    study1_cue_field,
)


PLACEHOLDER_MODEL = "UNSET_CONFIRMATORY_MODEL__OFFLINE_ONLY"
CUES = ("aligned", "reversed")
ARCHITECTURES = (ARCHITECTURE_C, ARCHITECTURE_D)


class ConfirmatoryRunnerError(RuntimeError):
    """Raised when a confirmatory runner source or offline gate fails."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfirmatoryRunnerError(f"required_file_missing:{path}") from exc


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError as exc:
        raise ConfirmatoryRunnerError(f"required_file_missing:{path}") from exc


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _opposite_arm_absent(
    packet: dict[str, Any], contract: dict[str, Any], current_arm: str
) -> bool:
    text = canonical_json(packet)
    return all(
        not spec["stimulus"] or spec["stimulus"] not in text
        for arm, spec in contract["materials"]["arms"].items()
        if arm != current_arm
    )


def _verify_frozen_manifest(
    repository_root: Path, freeze_manifest_path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = _read_json(freeze_manifest_path)
    checks = {
        "frozen_status": manifest.get("status")
        == "frozen_contracts_no_execution_authority",
        "contracts_frozen": manifest.get("contracts_frozen") is True,
        "paid_calls_disabled": manifest.get("paid_calls_authorized") is False,
        "api_calls_disabled": manifest.get("api_calls_authorized") is False,
        "no_authorization_file": manifest.get("authorization_file_created") is False,
        "freeze_was_offline": manifest.get("network_calls_during_freeze") == 0
        and manifest.get("model_called_during_freeze") is False,
        "freeze_audit_passed": manifest.get("offline_audit_all_checks_passed")
        is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ConfirmatoryRunnerError(f"freeze_manifest_not_ready:{failed}")

    receipt_path = freeze_manifest_path.parent / "freeze_receipt.json"
    receipt = _read_json(receipt_path)
    if receipt.get("freeze_manifest_sha256") != _file_sha256(freeze_manifest_path):
        raise ConfirmatoryRunnerError("freeze_receipt_manifest_hash_mismatch")
    if (
        receipt.get("api_calls_authorized") is not False
        or receipt.get("authorization_file_created") is not False
    ):
        raise ConfirmatoryRunnerError("freeze_receipt_improperly_authorizes_execution")

    audit_path = repository_root / manifest["offline_audit"]
    if _file_sha256(audit_path) != manifest["offline_audit_sha256"]:
        raise ConfirmatoryRunnerError("freeze_audit_hash_mismatch")
    audit = _read_json(audit_path)
    if (
        audit.get("all_checks_passed") is not True
        or audit.get("network_calls") != 0
        or audit.get("model_called") is not False
    ):
        raise ConfirmatoryRunnerError("freeze_audit_not_ready")

    contracts: list[dict[str, Any]] = []
    for row in manifest.get("contracts", []):
        contract_path = repository_root / row["path"]
        if _file_sha256(contract_path) != row["contract_file_sha256"]:
            raise ConfirmatoryRunnerError(
                f"contract_file_hash_mismatch:{row['contract_id']}"
            )
        contract = load_contract(contract_path)
        if contract["identity"]["study_id"] != row["contract_id"]:
            raise ConfirmatoryRunnerError(f"contract_id_mismatch:{row['contract_id']}")
        if contract["execution"]["contract_status"] != "frozen":
            raise ConfirmatoryRunnerError(f"contract_not_frozen:{row['contract_id']}")
        if contract["execution"]["paid_calls_authorized"] is not False:
            raise ConfirmatoryRunnerError(
                f"contract_paid_calls_enabled:{row['contract_id']}"
            )
        material_hash = normalized_material_hash(contract)
        if (
            material_hash != row["normalized_material_sha256"]
            or material_hash != contract["source"]["normalized_material_sha256"]
        ):
            raise ConfirmatoryRunnerError(
                f"contract_material_hash_mismatch:{row['contract_id']}"
            )
        contracts.append(contract)

    if len(contracts) != 8:
        raise ConfirmatoryRunnerError("unexpected_contract_count")
    if sum(len(c["materials"]["arms"]) for c in contracts) != manifest.get(
        "compiled_arm_packets"
    ):
        raise ConfirmatoryRunnerError("arm_packet_count_mismatch")
    return manifest, contracts


def run_confirmatory_offline_runner(
    repository_root: str | Path,
    freeze_manifest_path: str | Path,
    policy_path: str | Path,
    output_root: str | Path,
    *,
    persona_seed: int = 1,
) -> Path:
    """Compile and test one frozen batch without reading credentials or networking."""

    root = Path(repository_root).resolve()
    freeze_path = Path(freeze_manifest_path).resolve()
    policy_file = Path(policy_path).resolve()
    manifest, contracts = _verify_frozen_manifest(root, freeze_path)
    policy = _read_json(policy_file)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = Path(output_root).resolve() / run_id
    requests_dir = output / "requests"
    requests_dir.mkdir(parents=True, exist_ok=False)

    adapter = OpenAIResponsesDryRunAdapter(
        model_snapshot=PLACEHOLDER_MODEL,
        temperature=None,
        max_output_tokens=1024,
    )
    rows: list[dict[str, Any]] = []
    request_manifest: list[dict[str, Any]] = []
    persona_hashes: dict[str, set[str]] = defaultdict(set)
    visible_hashes: dict[tuple[str, str, str], dict[str, str]] = defaultdict(dict)

    sequence = 0
    for contract in contracts:
        study_id = contract["identity"]["study_id"]
        persona = build_source_matched_persona(contract, persona_seed)
        persona_hash = sha256_json(persona)
        contract_hash = _file_sha256(
            root
            / next(
                row["path"]
                for row in manifest["contracts"]
                if row["contract_id"] == study_id
            )
        )
        architectures = {
            ARCHITECTURE_C: ManualWhitelistArchitecture(contract),
            ARCHITECTURE_D: FirewallArchitecture(contract, policy),
        }
        for arm in contract["materials"]["arms"]:
            clean = study1_clean_fields(contract, persona, arm)
            for cue in CUES:
                cue_text = contract["research_restricted"][f"{cue}_hypothesis_text"]
                for architecture_name in ARCHITECTURES:
                    sequence += 1
                    context = BuildContext(
                        participant_id=persona["participant_id"],
                        current_arm=arm,
                        session_id=(
                            f"offline-{run_id}-{study_id}-{arm}-{cue}-{architecture_name}"
                        ),
                    )
                    architecture = architectures[architecture_name]
                    result = architecture.build(
                        [*clean, study1_cue_field(contract, cue)], context
                    )
                    if result.status != "ready" or result.packet_hash is None:
                        raise ConfirmatoryRunnerError(
                            f"packet_not_ready:{study_id}:{arm}:{cue}:{architecture_name}"
                        )
                    prepared = adapter.prepare(
                        result,
                        study_id=study_id,
                        contract_version=contract["identity"]["contract_version"],
                    )
                    body = json.loads(json.dumps(prepared.body))
                    body["metadata"].update(
                        {
                            "run_class": "study1_confirmatory_offline_runner",
                            "freeze_manifest_id": manifest["manifest_id"],
                            "architecture": architecture_name,
                            "arm": arm,
                            "cue": cue,
                            "sequence": str(sequence),
                            "network_enabled": "false",
                            "execution_authorized": "false",
                            "model_config_status": "unset",
                        }
                    )
                    model_visible_payload = {
                        "instructions": body["instructions"],
                        "input": body["input"],
                        "text": body["text"],
                    }
                    model_visible_text = canonical_json(model_visible_payload)

                    canary = f"CONFIRMATORY-CANARY-{study_id}-{arm}-{cue}"
                    canary_result = architecture.build(
                        [*clean, study1_cue_field(contract, cue, canary=canary)],
                        context,
                    )
                    canary_text = canonical_json(canary_result.packet)
                    expected_exposure = architecture_name == ARCHITECTURE_C
                    carrier_present = "summary_context" in result.packet
                    cue_present = cue_text in model_visible_text
                    canary_present = canary in canary_text
                    state_violations = validate_stateless_request(prepared)
                    response_schema_matches = (
                        result.packet["response_schema"]
                        == build_response_schema(contract)
                    )
                    scoring_metadata_absent = all(
                        marker not in canonical_json(result.packet)
                        for marker in (
                            "reverse_scored",
                            "aligned_hypothesis_text",
                            "reversed_hypothesis_text",
                            "primary_estimand",
                        )
                    )
                    row = {
                        "sequence": sequence,
                        "study_id": study_id,
                        "contract_version": contract["identity"]["contract_version"],
                        "contract_file_sha256": contract_hash,
                        "material_sha256": normalized_material_hash(contract),
                        "arm": arm,
                        "cue": cue,
                        "architecture": architecture_name,
                        "participant_id": persona["participant_id"],
                        "persona_hash": persona_hash,
                        "packet_hash": result.packet_hash,
                        "request_hash": sha256_json(body),
                        "model_visible_hash": sha256_json(model_visible_payload),
                        "packet_ready": True,
                        "persona_fields_match_contract": set(persona)
                        == set(contract["population"]["required_persona_fields"]),
                        "carrier_present": carrier_present,
                        "cue_present": cue_present,
                        "canary_present": canary_present,
                        "expected_exposure": expected_exposure,
                        "exposure_behavior_correct": (
                            carrier_present == expected_exposure
                            and cue_present == expected_exposure
                            and canary_present == expected_exposure
                        ),
                        "opposite_arm_absent": _opposite_arm_absent(
                            result.packet, contract, arm
                        ),
                        "response_schema_matches": response_schema_matches,
                        "scoring_metadata_absent": scoring_metadata_absent,
                        "state_violations": "|".join(state_violations),
                        "placeholder_model_only": body["model"] == PLACEHOLDER_MODEL,
                        "temperature_absent": "temperature" not in body,
                        "network_calls": 0,
                        "model_called": False,
                        "api_calls_authorized": False,
                    }
                    rows.append(row)
                    persona_hashes[study_id].add(persona_hash)
                    visible_hashes[(study_id, arm, architecture_name)][cue] = row[
                        "model_visible_hash"
                    ]

                    filename = (
                        f"{sequence:04d}__{study_id}__{arm}__{cue}__"
                        f"{architecture_name}.json"
                    )
                    request_path = requests_dir / filename
                    _write_json(
                        request_path,
                        {
                            "dry_run": True,
                            "network_calls": 0,
                            "model_called": False,
                            "api_calls_authorized": False,
                            "audit": row,
                            "body": body,
                        },
                    )
                    request_manifest.append(
                        {
                            "sequence": sequence,
                            "request_file": _relative(root, request_path),
                            "request_file_sha256": _file_sha256(request_path),
                            "request_hash": row["request_hash"],
                            "packet_hash": row["packet_hash"],
                        }
                    )

    expected_requests = manifest["compiled_arm_packets"] * len(CUES) * len(
        ARCHITECTURES
    )
    row_gate_fields = (
        "packet_ready",
        "persona_fields_match_contract",
        "exposure_behavior_correct",
        "opposite_arm_absent",
        "response_schema_matches",
        "scoring_metadata_absent",
        "placeholder_model_only",
        "temperature_absent",
    )
    gates = {
        "frozen_manifest_bound": len(_file_sha256(freeze_path)) == 64,
        "eight_contracts": len(contracts) == 8,
        "all_arm_packets_compiled": len(rows) == expected_requests,
        "one_persona_replayed_per_contract": all(
            len(hashes) == 1 for hashes in persona_hashes.values()
        ),
        "all_row_gates_pass": all(
            all(row[field] is True for field in row_gate_fields) for row in rows
        ),
        "all_requests_stateless": all(row["state_violations"] == "" for row in rows),
        "architecture_c_changes_across_cues": all(
            cue_hashes.get("aligned") != cue_hashes.get("reversed")
            for (study, arm, architecture), cue_hashes in visible_hashes.items()
            if architecture == ARCHITECTURE_C
        ),
        "architecture_d_invariant_across_cues": all(
            cue_hashes.get("aligned") == cue_hashes.get("reversed")
            for (study, arm, architecture), cue_hashes in visible_hashes.items()
            if architecture == ARCHITECTURE_D
        ),
        "no_network_calls": all(row["network_calls"] == 0 for row in rows),
        "no_model_calls": all(row["model_called"] is False for row in rows),
        "no_api_authorization": all(
            row["api_calls_authorized"] is False for row in rows
        ),
        "model_and_sampling_config_unset": all(
            row["placeholder_model_only"] and row["temperature_absent"]
            for row in rows
        ),
    }

    audit_path = output / "audit.csv"
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    request_manifest_path = output / "request_manifest.jsonl"
    _write_jsonl(request_manifest_path, request_manifest)

    summary = {
        "run_id": run_id,
        "run_class": "study1_confirmatory_offline_runner",
        "status": "offline_test_pass" if all(gates.values()) else "offline_test_fail",
        "freeze_manifest": _relative(root, freeze_path),
        "freeze_manifest_sha256": _file_sha256(freeze_path),
        "freeze_manifest_id": manifest["manifest_id"],
        "batch_code": manifest["manifest_id"].split("-")[3],
        "batch_material_set_sha256": manifest["batch_material_set_sha256"],
        "batch_contract_set_sha256": manifest["batch_contract_set_sha256"],
        "access_policy": _relative(root, policy_file),
        "access_policy_sha256": _file_sha256(policy_file),
        "contracts": len(contracts),
        "arm_packets": manifest["compiled_arm_packets"],
        "cues": list(CUES),
        "architectures": list(ARCHITECTURES),
        "request_templates": len(rows),
        "expected_request_templates": expected_requests,
        "persona_seed": persona_seed,
        "provider_envelope": "openai_responses_placeholder",
        "model_snapshot": PLACEHOLDER_MODEL,
        "model_configuration_status": "unset",
        "sampling_plan_status": "unset",
        "network_calls": 0,
        "model_called": False,
        "paid_calls_authorized": False,
        "api_calls_authorized": False,
        "authorization_file_created": False,
        "offline_ready_for_execution_config": all(gates.values()),
        "offline_ready_for_api_authorization": False,
        "gates": gates,
        "gates_passed": sum(gates.values()),
        "gates_total": len(gates),
        "interpretation": (
            "The frozen contracts compile deterministically and the C/D information-flow "
            "contrast behaves as designed. This package has a placeholder model and no "
            "sampling plan, so it cannot authorize or execute API calls."
        ),
    }
    summary_path = output / "summary.json"
    _write_json(summary_path, summary)

    request_set_sha256 = sha256_json(
        [
            {
                "sequence": row["sequence"],
                "request_file_sha256": row["request_file_sha256"],
                "request_hash": row["request_hash"],
            }
            for row in request_manifest
        ]
    )
    runner_manifest = {
        "runner_manifest_id": (
            f"{manifest['manifest_id']}-OFFLINE-RUNNER-{run_id}"
        ),
        "status": summary["status"],
        "freeze_manifest_sha256": summary["freeze_manifest_sha256"],
        "runner_module": _relative(root, Path(__file__).resolve()),
        "runner_module_sha256": _file_sha256(Path(__file__).resolve()),
        "summary": _relative(root, summary_path),
        "summary_sha256": _file_sha256(summary_path),
        "audit_csv": _relative(root, audit_path),
        "audit_csv_sha256": _file_sha256(audit_path),
        "request_manifest": _relative(root, request_manifest_path),
        "request_manifest_sha256": _file_sha256(request_manifest_path),
        "request_set_sha256": request_set_sha256,
        "request_templates": len(rows),
        "network_calls": 0,
        "model_called": False,
        "api_calls_authorized": False,
        "authorization_file_created": False,
    }
    runner_manifest_path = output / "runner_manifest.json"
    _write_json(runner_manifest_path, runner_manifest)
    _write_json(
        output / "offline_receipt.json",
        {
            "runner_manifest": _relative(root, runner_manifest_path),
            "runner_manifest_sha256": _file_sha256(runner_manifest_path),
            "request_set_sha256": request_set_sha256,
            "offline_test_passed": all(gates.values()),
            "network_calls": 0,
            "model_called": False,
            "api_calls_authorized": False,
        },
    )

    readme = [
        f"# Study 1 Confirmatory {summary['batch_code']} Offline Runner",
        "",
        f"Run ID: `{run_id}`  ",
        f"Status: `{summary['status']}`  ",
        f"Frozen contracts: {len(contracts)}  ",
        f"Arm packets: {manifest['compiled_arm_packets']}  ",
        f"C/D by aligned/reversed request templates: {len(rows)}  ",
        "Network calls: 0  ",
        "Model calls: 0  ",
        "API authorization: none",
        "",
        "## Boundary",
        "",
        "This package verifies frozen-source integrity, persona replay, request isolation, "
        "strict response schemas, and the expected C-versus-D cue exposure behavior. The "
        "model is intentionally a placeholder and the sampling plan is unset. The package "
        "therefore cannot be used for live execution or treated as an API authorization.",
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "|---|---|",
    ]
    readme.extend(
        f"| `{name}` | {'PASS' if passed else 'FAIL'} |"
        for name, passed in gates.items()
    )
    (output / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    if not all(gates.values()):
        raise ConfirmatoryRunnerError("offline_runner_gate_failure")
    return output


def inspect_unfrozen_batch(
    repository_root: str | Path, draft_manifest_path: str | Path
) -> dict[str, Any]:
    """Verify an unfrozen batch and state why a frozen runner cannot be built."""

    root = Path(repository_root).resolve()
    path = Path(draft_manifest_path).resolve()
    manifest = _read_json(path)
    contracts_valid = True
    hashes_valid = True
    for row in manifest.get("contracts", []):
        contract_path = root / row["path"]
        hashes_valid = hashes_valid and _file_sha256(contract_path) == row[
            "contract_file_sha256"
        ]
        contract = load_contract(contract_path)
        contracts_valid = contracts_valid and contract["execution"][
            "contract_status"
        ] in {"draft", "dual_reviewed"}
        hashes_valid = hashes_valid and normalized_material_hash(contract) == row[
            "draft_material_sha256"
        ]
    audit_path = root / manifest["offline_audit"]
    audit_hash_valid = _file_sha256(audit_path) == manifest["offline_audit_sha256"]
    audit = _read_json(audit_path)
    draft_audit_passed = (
        audit_hash_valid
        and audit.get("all_checks_passed") is True
        and audit.get("network_calls") == 0
        and audit.get("model_called") is False
    )
    rejection_passed = False
    try:
        _verify_frozen_manifest(root, path)
    except ConfirmatoryRunnerError as exc:
        rejection_passed = str(exc).startswith("freeze_manifest_not_ready:")
    return {
        "manifest": _relative(root, path),
        "manifest_sha256": _file_sha256(path),
        "contracts": len(manifest.get("contracts", [])),
        "contract_status": manifest.get("status"),
        "contracts_frozen": manifest.get("contracts_frozen") is True,
        "contracts_valid": contracts_valid,
        "contract_hashes_valid": hashes_valid,
        "draft_arm_packets": audit.get("compiled_arm_packets"),
        "draft_offline_audit_passed": draft_audit_passed,
        "runner_fail_closed_test_passed": rejection_passed,
        "frozen_runner_built": False,
        "api_calls_authorized": False,
        "blocking_gate": "explicit PI freeze decision and formal frozen-material hashes",
    }
