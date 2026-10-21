"""Compile and audit the five Study 1 engineering-pilot contracts offline.

This module has no network client and never reads credentials. It produces
provider-shaped request templates only so information-flow, persona replay,
and response schemas can be checked before contracts are frozen.
"""

from __future__ import annotations

import copy
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .architectures import FirewallArchitecture, ManualWhitelistArchitecture
from .hashing import canonical_json, sha256_json
from .models import BuildContext, PacketBuildResult, TaggedField
from .providers import OpenAIResponsesDryRunAdapter, validate_stateless_request
from .study1_contract import load_contract, normalized_material_hash


ARCHITECTURE_C = "C_fresh_context_manual_whitelist"
ARCHITECTURE_D = "D_labeled_causal_firewall"
SUPPORTED_PERSONA_FIELDS = {
    "participant_id",
    "adult",
    "country_context",
    "student_context",
}
FORBIDDEN_PACKET_FIELDS = {
    "hypothesis_text",
    "expected_direction",
    "other_arm_stimulus",
    "human_benchmark",
    "derived_study_summary",
    "handoff_history",
    "session_context",
    "retry_context",
    "tool_context",
    "audit_feedback",
}


class Study1PrefreezeError(RuntimeError):
    """Raised when an offline pre-freeze invariant cannot be satisfied."""


def validate_engineering_pilot_config(config: dict[str, Any]) -> None:
    """Validate the approved single-model pilot plan without authorizing calls."""

    decoding = config.get("decoding", {})
    sampling = config.get("sampling_plan", {})
    expected_cells = config.get("expected_total_cells")
    stages = sampling.get("behavioral_stage_draws_per_cell", [])

    checks = {
        "configuration_must_be_frozen": (
            config.get("configuration_status") == "frozen"
            and config.get("config_version") == "1.0.0-frozen"
        ),
        "provider_must_be_openai": config.get("provider") == "openai",
        "model_snapshot_must_be_selected": (
            config.get("model_snapshot") == "gpt-5.4-mini-2026-03-17"
        ),
        "reasoning_effort_must_be_none": (
            decoding.get("reasoning_effort") == "none"
        ),
        "temperature_must_be_one": decoding.get("temperature") == 1.0,
        "top_p_must_be_unset": decoding.get("top_p") == "unset",
        "seed_must_be_unset": decoding.get("seed") == "unset",
        "single_model_pilot": sampling.get("model_count") == 1,
        "behavioral_stages_sum_to_total": (
            stages == [10, 20]
            and sum(stages) == sampling.get("behavioral_draws_per_cell")
        ),
        "compatibility_call_count_matches": (
            sampling.get("expected_compatibility_calls")
            == expected_cells * sampling.get("compatibility_draws_per_cell", -1)
        ),
        "behavioral_call_count_matches": (
            sampling.get("expected_behavioral_calls")
            == expected_cells * sampling.get("behavioral_draws_per_cell", -1)
        ),
        "maximum_call_count_matches": (
            sampling.get("planned_maximum_calls")
            == sampling.get("expected_compatibility_calls", -1)
            + sampling.get("expected_behavioral_calls", -1)
        ),
        "pilot_excluded_from_confirmatory_analysis": (
            sampling.get("pilot_included_in_confirmatory_analysis") is False
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise Study1PrefreezeError(f"invalid_engineering_pilot_config:{failed}")


def build_source_matched_persona(
    contract: dict[str, Any],
    persona_seed: int,
) -> dict[str, Any]:
    """Build only the coarse, prereviewed persona fields required by a contract."""

    required = tuple(contract["population"]["required_persona_fields"])
    unsupported = set(required) - SUPPORTED_PERSONA_FIELDS
    if unsupported:
        raise Study1PrefreezeError(
            f"unsupported_persona_fields:{sorted(unsupported)}"
        )

    available: dict[str, Any] = {
        "participant_id": (
            f"{contract['identity']['study_id']}-P-{persona_seed:08d}"
        ),
        "adult": True,
        "country_context": "United States",
        "student_context": "U.S. undergraduate business-school student",
    }
    return {field: available[field] for field in required}


def participant_outcome_items(
    contract: dict[str, Any], arm: str | None = None
) -> dict[str, Any]:
    """Expose questions and bounds without exposing scoring or hypotheses."""

    items: list[dict[str, Any]] = []
    for outcome in contract["outcomes"].values():
        for item in outcome["items"]:
            text = item.get("text_by_arm", {}).get(arm, item["text"])
            visible_item = {
                "item_id": item["item_id"],
                "text": text,
                "minimum": item["minimum"],
                "integer_only": bool(item.get("integer_only", False)),
            }
            if item["maximum"] is not None:
                visible_item["maximum"] = item["maximum"]
            items.append(visible_item)
    return {
        "response_instruction": contract["materials"]["response_instruction"],
        "items": items,
    }


def build_response_schema(contract: dict[str, Any]) -> dict[str, Any]:
    """Create one strict flat schema containing every source outcome item."""

    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []
    for outcome in contract["outcomes"].values():
        for item in outcome["items"]:
            item_id = item["item_id"]
            if item_id in properties:
                raise Study1PrefreezeError(f"duplicate_item_id:{item_id}")
            property_schema: dict[str, Any] = {
                "type": "integer" if item.get("integer_only") else "number",
                "minimum": item["minimum"],
            }
            if item["maximum"] is not None:
                property_schema["maximum"] = item["maximum"]
            properties[item_id] = property_schema
            required.append(item_id)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def study1_clean_fields(
    contract: dict[str, Any],
    persona: dict[str, Any],
    arm: str,
) -> list[TaggedField]:
    """Compile the legal participant packet for one arm."""

    participant_id = persona["participant_id"]
    materials = contract["materials"]
    if arm not in materials["arms"]:
        raise Study1PrefreezeError(f"unknown_arm:{arm}")
    return [
        TaggedField(
            field_id="participant_role",
            value=materials["participant_role"],
            label="PARTICIPANT_VISIBLE",
            provenance=("experiment_contract.materials.participant_role",),
            stage="behavior_generation",
            arm_scope="common",
        ),
        TaggedField(
            field_id="persona_state",
            value=persona,
            label="PARTICIPANT_SELF",
            provenance=("study1_source_matched_persona",),
            stage="pre_treatment",
            arm_scope="participant",
            participant_id=participant_id,
        ),
        TaggedField(
            field_id="common_scenario",
            value=materials["common_scenario"],
            label="PARTICIPANT_VISIBLE",
            provenance=("experiment_contract.materials.common_scenario",),
            stage="behavior_generation",
            arm_scope="common",
        ),
        TaggedField(
            field_id="current_stimulus",
            value=materials["arms"][arm]["stimulus"],
            label="PARTICIPANT_VISIBLE",
            provenance=(f"experiment_contract.materials.arms.{arm}.stimulus",),
            stage="behavior_generation",
            arm_scope="current_arm",
            source_arm=arm,
        ),
        TaggedField(
            field_id="outcome_items",
            value=participant_outcome_items(contract, arm),
            label="PARTICIPANT_VISIBLE",
            provenance=("experiment_contract.outcomes",),
            stage="behavior_generation",
            arm_scope="common",
        ),
        TaggedField(
            field_id="response_schema",
            value=build_response_schema(contract),
            label="PARTICIPANT_VISIBLE",
            provenance=("compiled_strict_response_schema",),
            stage="behavior_generation",
            arm_scope="common",
        ),
    ]


def study1_cue_field(
    contract: dict[str, Any],
    cue: str,
    *,
    canary: str | None = None,
) -> TaggedField:
    """Build the same contaminated summary supplied to C and attempted in D."""

    key_by_cue = {
        "aligned": "aligned_hypothesis_text",
        "reversed": "reversed_hypothesis_text",
    }
    try:
        value = contract["research_restricted"][key_by_cue[cue]]
    except KeyError as exc:
        raise Study1PrefreezeError(f"unsupported_cue:{cue}") from exc
    if canary:
        value = f"{value} AUDIT_CANARY={canary}"
    return TaggedField(
        field_id="summary_context",
        value=value,
        label="PARTICIPANT_VISIBLE",
        provenance=("hypothesis_text", "derived_summary_agent"),
        stage="handoff",
        arm_scope="study",
        lineage_labels=("RESEARCH_RESTRICTED",),
    )


def _schema_matches_contract(
    schema: dict[str, Any],
    contract: dict[str, Any],
) -> bool:
    return schema == build_response_schema(contract)


def _opposite_arm_absent(
    packet: dict[str, Any],
    contract: dict[str, Any],
    current_arm: str,
) -> bool:
    text = canonical_json(packet)
    for arm, spec in contract["materials"]["arms"].items():
        if arm == current_arm:
            continue
        stimulus = spec["stimulus"]
        if stimulus and stimulus in text:
            return False
    return "other_arm_stimulus" not in packet


def _forbidden_system_fields_absent(packet: dict[str, Any]) -> bool:
    return not (set(packet) & FORBIDDEN_PACKET_FIELDS)


def _architecture_map(
    contract: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        ARCHITECTURE_C: ManualWhitelistArchitecture(contract),
        ARCHITECTURE_D: FirewallArchitecture(contract, policy),
    }


def _build_canary_result(
    architecture: Any,
    clean_fields: Iterable[TaggedField],
    contract: dict[str, Any],
    cue: str,
    context: BuildContext,
    canary: str,
) -> PacketBuildResult:
    fields = list(clean_fields)
    fields.append(study1_cue_field(contract, cue, canary=canary))
    return architecture.build(fields, context)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _markdown_report(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Study 1 Pre Freeze No API Audit",
        "",
        f"Run ID: `{summary['run_id']}`  ",
        f"Contracts: {summary['contracts']}  ",
        f"Compiled request templates: {summary['cells']}  ",
        f"Provider: `{summary['provider']}`  ",
        f"Model snapshot: `{summary['model_snapshot']}`  ",
        f"Temperature: `{summary['decoding']['temperature']}`  ",
        "Network calls: 0  ",
        f"Contract state: {summary['contract_status']}; broad paid-call authorization disabled",
        "",
        "## Decision",
        "",
        (
            "All structural gates passed. The five engineering-pilot contracts and "
            "execution configuration are frozen. Live execution still requires a "
            "separate phase-specific authorization."
            if summary["ready_for_freeze_preparation"]
            else "One or more structural gates failed. Do not call an API."
        ),
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "|---|---|",
    ]
    for gate, passed in summary["gates"].items():
        lines.append(f"| `{gate}` | {'PASS' if passed else 'FAIL'} |")
    sampling = summary["sampling_plan"]
    lines.extend(
        [
            "",
            "## Approved Pilot Sampling Plan",
            "",
            f"- Compatibility smoke: {sampling['expected_compatibility_calls']} calls "
            f"({sampling['compatibility_draws_per_cell']} per cell).",
            f"- Behavioral pilot: {sampling['expected_behavioral_calls']} calls "
            f"({sampling['behavioral_stage_draws_per_cell']} per cell, "
            f"total {sampling['behavioral_draws_per_cell']}).",
            f"- Planned maximum after separate paid-call approvals: "
            f"{sampling['planned_maximum_calls']} calls.",
            "- Pilot outputs are excluded from the Study 1 confirmatory analysis.",
        ]
    )
    lines.extend(
        [
            "",
            "## Contract Summary",
            "",
            "| Study | Cells | Persona fields | Material hash |",
            "|---|---:|---|---|",
        ]
    )
    for study_id, spec in summary["by_study"].items():
        fields = ", ".join(spec["persona_fields"])
        lines.append(
            f"| `{study_id}` | {spec['cells']} | {fields} | `{spec['material_hash']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "This audit verifies deterministic request construction and information "
            "separation only. It contains no model responses and provides no behavioral "
            "or human-fidelity evidence. A separate phase-specific authorization is "
            "required before any live provider call.",
            "",
        ]
    )
    return "\n".join(lines)


def run_study1_prefreeze_audit(
    contract_paths: Iterable[str | Path],
    policy: dict[str, Any],
    config: dict[str, Any],
    output_root: str | Path,
) -> Path:
    """Compile the full 40-cell Study 1 matrix without network access."""

    if config.get("network_enabled") is not False:
        raise Study1PrefreezeError("network_must_be_disabled")
    if config.get("paid_calls_authorized") is not False:
        raise Study1PrefreezeError("paid_calls_must_be_unauthorized")
    validate_engineering_pilot_config(config)

    contracts = [load_contract(path) for path in contract_paths]
    if len(contracts) != config["expected_contracts"]:
        raise Study1PrefreezeError("unexpected_contract_count")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = Path(output_root) / run_id
    requests_dir = output / "requests"
    requests_dir.mkdir(parents=True, exist_ok=False)

    rows: list[dict[str, Any]] = []
    for contract in contracts:
        study_id = contract["identity"]["study_id"]
        execution = contract["execution"]
        if execution["contract_status"] != config["expected_contract_status"]:
            raise Study1PrefreezeError(f"unexpected_contract_status:{study_id}")
        if execution["paid_calls_authorized"]:
            raise Study1PrefreezeError(f"broad_paid_calls_authorized:{study_id}")
        computed_material_hash = normalized_material_hash(contract)
        if (
            contract["source"]["normalized_material_sha256"]
            != computed_material_hash
        ):
            raise Study1PrefreezeError(f"frozen_material_hash_mismatch:{study_id}")

        persona = build_source_matched_persona(contract, config["persona_seed"])
        persona_hash = sha256_json(persona)
        architectures = _architecture_map(contract, policy)
        adapter = OpenAIResponsesDryRunAdapter(
            model_snapshot=config["model_snapshot"],
            temperature=float(config["decoding"]["temperature"]),
            max_output_tokens=config["max_output_tokens"],
        )
        contract_hash = sha256_json(contract)

        for arm in contract["materials"]["arms"]:
            clean = study1_clean_fields(contract, persona, arm)
            for cue in config["hypothesis_cues"]:
                cue_text = contract["research_restricted"][
                    f"{cue}_hypothesis_text"
                ]
                for architecture_name in config["architectures"]:
                    architecture = architectures[architecture_name]
                    fields = [*clean, study1_cue_field(contract, cue)]
                    context = BuildContext(
                        participant_id=persona["participant_id"],
                        current_arm=arm,
                        session_id=(
                            f"fresh-{run_id}-{study_id}-{arm}-{cue}-{architecture_name}"
                        ),
                    )
                    result = architecture.build(fields, context)
                    if result.status != "ready" or result.packet_hash is None:
                        raise Study1PrefreezeError(
                            f"packet_not_ready:{study_id}:{arm}:{cue}:{architecture_name}"
                        )
                    prepared = adapter.prepare(
                        result,
                        study_id=study_id,
                        contract_version=contract["identity"]["contract_version"],
                    )
                    body = copy.deepcopy(prepared.body)
                    body["metadata"].update(
                        {
                            "run_class": config["run_class"],
                            "architecture": architecture_name,
                            "arm": arm,
                            "cue": cue,
                            "network_enabled": "false",
                        }
                    )

                    canary = f"S1CANARY-{study_id}-{arm}-{cue}"
                    canary_result = _build_canary_result(
                        architecture,
                        clean,
                        contract,
                        cue,
                        context,
                        canary,
                    )
                    canary_text = canonical_json(canary_result.packet)
                    model_visible_text = canonical_json(prepared.model_visible_payload)
                    schema = result.packet["response_schema"]
                    core_forbidden_absent = _forbidden_system_fields_absent(
                        result.packet
                    )
                    carrier_present = config["cue_carrier_field"] in result.packet
                    cue_present = cue_text in model_visible_text
                    canary_present = canary in canary_text
                    expected_exposure = architecture_name == ARCHITECTURE_C

                    row = {
                        "study_id": study_id,
                        "contract_version": contract["identity"]["contract_version"],
                        "architecture": architecture_name,
                        "arm": arm,
                        "cue": cue,
                        "persona_seed": config["persona_seed"],
                        "provider": config["provider"],
                        "model_snapshot": body["model"],
                        "reasoning_effort": body["reasoning"]["effort"],
                        "temperature": body.get("temperature"),
                        "top_p_present": "top_p" in body,
                        "seed_present": "seed" in body,
                        "participant_id": persona["participant_id"],
                        "persona_hash": persona_hash,
                        "persona_fields_match_contract": (
                            set(persona)
                            == set(contract["population"]["required_persona_fields"])
                        ),
                        "packet_status": result.status,
                        "packet_hash": result.packet_hash,
                        "model_visible_hash": prepared.model_visible_hash,
                        "request_hash": sha256_json(body),
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
                        "forbidden_system_fields_absent": core_forbidden_absent,
                        "response_schema_matches": _schema_matches_contract(
                            schema, contract
                        ),
                        "scoring_metadata_absent": (
                            "reverse_scored" not in canonical_json(result.packet)
                            and "aligned_hypothesis_text"
                            not in canonical_json(result.packet)
                            and "reversed_hypothesis_text"
                            not in canonical_json(result.packet)
                        ),
                        "state_violations": "|".join(
                            validate_stateless_request(prepared)
                        ),
                        "network_calls": 0,
                        "model_called": False,
                        "contract_hash": contract_hash,
                        "material_hash": normalized_material_hash(contract),
                        "stored_material_hash": contract["source"][
                            "normalized_material_sha256"
                        ],
                        "material_hash_matches": (
                            contract["source"]["normalized_material_sha256"]
                            == normalized_material_hash(contract)
                        ),
                    }
                    rows.append(row)

                    filename = (
                        f"{study_id}__{arm}__{cue}__{architecture_name}.json"
                    )
                    _write_json(
                        requests_dir / filename,
                        {
                            "dry_run": True,
                            "network_calls": 0,
                            "model_called": False,
                            "audit": row,
                            "body": body,
                        },
                    )

    d_hashes: dict[tuple[str, str], set[str]] = {}
    c_hashes: dict[tuple[str, str], set[str]] = {}
    persona_hashes: dict[str, set[str]] = {}
    by_study: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = (row["study_id"], row["arm"])
        target = d_hashes if row["architecture"] == ARCHITECTURE_D else c_hashes
        target.setdefault(key, set()).add(row["model_visible_hash"])
        persona_hashes.setdefault(row["study_id"], set()).add(row["persona_hash"])
        spec = by_study.setdefault(
            row["study_id"],
            {
                "cells": 0,
                "persona_fields": [],
                "material_hash": row["material_hash"],
                "contract_hash": row["contract_hash"],
            },
        )
        spec["cells"] += 1

    for contract in contracts:
        by_study[contract["identity"]["study_id"]]["persona_fields"] = contract[
            "population"
        ]["required_persona_fields"]

    gates = {
        "network_disabled": config["network_enabled"] is False,
        "single_openai_model_selected": (
            config["provider"] == "openai"
            and config["model_snapshot"] == "gpt-5.4-mini-2026-03-17"
        ),
        "decoding_configuration_matches_decision": all(
            row["reasoning_effort"] == "none"
            and row["temperature"] == 1.0
            and not row["top_p_present"]
            and not row["seed_present"]
            for row in rows
        ),
        "sampling_plan_counts_match": (
            config["sampling_plan"]["expected_compatibility_calls"] == 40
            and config["sampling_plan"]["expected_behavioral_calls"] == 1200
            and config["sampling_plan"]["planned_maximum_calls"] == 1240
            and config["sampling_plan"]["behavioral_stage_draws_per_cell"]
            == [10, 20]
        ),
        "pilot_excluded_from_confirmatory_analysis": (
            config["sampling_plan"]["pilot_included_in_confirmatory_analysis"]
            is False
        ),
        "contract_count": len(contracts) == config["expected_contracts"],
        "cell_count": len(rows) == config["expected_total_cells"],
        "cells_per_contract": all(
            spec["cells"] == config["expected_cells_per_contract"]
            for spec in by_study.values()
        ),
        "all_packets_ready": all(row["packet_status"] == "ready" for row in rows),
        "all_requests_stateless": all(not row["state_violations"] for row in rows),
        "persona_fields_source_matched": all(
            row["persona_fields_match_contract"] for row in rows
        ),
        "persona_replayed_across_all_cells": all(
            len(hashes) == 1 for hashes in persona_hashes.values()
        ),
        "c_cues_and_canaries_reachable": all(
            row["exposure_behavior_correct"]
            for row in rows
            if row["architecture"] == ARCHITECTURE_C
        ),
        "d_cues_and_canaries_blocked": all(
            row["exposure_behavior_correct"]
            for row in rows
            if row["architecture"] == ARCHITECTURE_D
        ),
        "d_cue_hash_invariance": all(
            len(hashes) == 1 for hashes in d_hashes.values()
        ),
        "c_cue_hash_separation": all(
            len(hashes) == len(config["hypothesis_cues"])
            for hashes in c_hashes.values()
        ),
        "opposite_arm_absent": all(row["opposite_arm_absent"] for row in rows),
        "forbidden_system_fields_absent": all(
            row["forbidden_system_fields_absent"] for row in rows
        ),
        "response_schemas_match_contracts": all(
            row["response_schema_matches"] for row in rows
        ),
        "scoring_metadata_absent": all(
            row["scoring_metadata_absent"] for row in rows
        ),
        "contracts_are_frozen": all(
            contract["execution"]["contract_status"] == "frozen"
            for contract in contracts
        ),
        "broad_paid_calls_unauthorized": all(
            contract["execution"]["paid_calls_authorized"] is False
            for contract in contracts
        ),
        "frozen_material_hashes_match": all(
            row["material_hash_matches"] for row in rows
        ),
    }
    summary = {
        "run_id": run_id,
        "run_class": config["run_class"],
        "network_calls": 0,
        "model_called": False,
        "provider": config["provider"],
        "model_snapshot": config["model_snapshot"],
        "decoding": config["decoding"],
        "sampling_plan": config["sampling_plan"],
        "contract_status": config["expected_contract_status"],
        "contracts": len(contracts),
        "cells": len(rows),
        "gates": gates,
        "gates_passed": sum(gates.values()),
        "gates_total": len(gates),
        "ready_for_freeze_preparation": all(gates.values()),
        "policy_hash": sha256_json(policy),
        "config_hash": sha256_json(config),
        "by_study": by_study,
        "interpretation": (
            "Offline structural evidence only. No provider was contacted, no model "
            "response was generated. Contracts and execution configuration were "
            "already frozen before this audit."
        ),
    }

    _write_csv(output / "audit_report.csv", rows)
    with (output / "manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    _write_json(output / "summary.json", summary)
    (output / "PREFREEZE_AUDIT_REPORT.md").write_text(
        _markdown_report(summary, rows), encoding="utf-8"
    )
    return output
