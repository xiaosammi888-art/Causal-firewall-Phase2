"""Validation helpers for Study 1 experiment contracts.

The validator deliberately checks the cross-field invariants that JSON Schema
cannot express concisely. It has no third-party dependency and performs no API
calls.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class Study1ContractError(ValueError):
    """Raised when a Study 1 contract violates a frozen invariant."""


def load_contract(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        contract = json.load(handle)
    validate_contract(contract)
    return contract


def validate_contract(contract: dict[str, Any]) -> None:
    required = {
        "identity",
        "source",
        "design",
        "population",
        "materials",
        "outcomes",
        "research_restricted",
        "participant_packet",
        "execution",
    }
    missing = required - contract.keys()
    if missing:
        raise Study1ContractError(f"missing top-level sections: {sorted(missing)}")

    arms = contract["materials"]["arms"]
    design_type = contract["design"]["type"]
    expected_arm_count = {
        "two_arm_between_subjects": 2,
        "three_arm_between_subjects": 3,
        "four_arm_between_subjects": 4,
        "factorial_between_subjects_2x2": 4,
        "six_arm_between_subjects": 6,
        "factorial_between_subjects_2x3": 6,
        "factorial_between_subjects_2x2x2": 8,
    }.get(design_type)
    if expected_arm_count is None:
        raise Study1ContractError(f"unsupported design type: {design_type}")
    if len(arms) != expected_arm_count:
        raise Study1ContractError(
            f"{design_type} requires exactly {expected_arm_count} arms"
        )

    primary_name = contract["design"]["primary_outcome"]
    outcomes = contract["outcomes"]
    if primary_name not in outcomes:
        raise Study1ContractError("design.primary_outcome is not defined in outcomes")
    primary_roles = [name for name, spec in outcomes.items() if spec["role"] == "primary"]
    if primary_roles != [primary_name]:
        raise Study1ContractError("exactly one outcome must be primary")

    global_item_ids: set[str] = set()
    for outcome_name, spec in outcomes.items():
        if spec.get("model_may_write_aggregate") is not False:
            raise Study1ContractError(
                f"{outcome_name}: aggregate outcomes must be deterministically encoded"
            )
        item_ids: set[str] = set()
        for item in spec["items"]:
            if item["item_id"] in item_ids:
                raise Study1ContractError(
                    f"{outcome_name}: duplicate item_id {item['item_id']}"
                )
            item_ids.add(item["item_id"])
            if item["item_id"] in global_item_ids:
                raise Study1ContractError(
                    f"duplicate item_id across outcomes: {item['item_id']}"
                )
            global_item_ids.add(item["item_id"])
            if item["maximum"] is not None and item["minimum"] >= item["maximum"]:
                raise Study1ContractError(
                    f"{outcome_name}.{item['item_id']}: minimum must be below maximum"
                )
            text_by_arm = item.get("text_by_arm", {})
            unknown_arms = set(text_by_arm) - set(arms)
            if unknown_arms:
                raise Study1ContractError(
                    f"{outcome_name}.{item['item_id']}: unknown text_by_arm keys "
                    f"{sorted(unknown_arms)}"
                )

    source = contract["source"]
    required_source_fields = {
        "source_article",
        "source_article_url",
        "material_policy",
        "authorized_normalizations",
        "omitted_source_measures",
    }
    missing_source = required_source_fields - source.keys()
    if missing_source:
        raise Study1ContractError(
            f"missing source-provenance fields: {sorted(missing_source)}"
        )
    expected_policy = (
        "source_faithful_experimental_content_with_standardized_simulation_wrapper"
    )
    if source["material_policy"] != expected_policy:
        raise Study1ContractError("unexpected source-material policy")

    restricted = contract["research_restricted"]
    if restricted["human_benchmark_status"] != "EMBARGOED_NOT_IN_CONTRACT":
        raise Study1ContractError("human benchmark must remain outside the runnable contract")
    if restricted["other_arm_visibility"] != "deny":
        raise Study1ContractError("opposite-arm material must be denied")

    forbidden = set(contract["participant_packet"]["forbidden_information_classes"])
    required_forbidden = {
        "HYPOTHESIS_CUE",
        "HUMAN_BENCHMARK",
        "OTHER_ARM",
        "DERIVED_STUDY_SUMMARY",
    }
    if not required_forbidden <= forbidden:
        raise Study1ContractError("participant packet is missing a required information-class ban")

    execution = contract["execution"]
    if execution["contract_status"] == "draft" and execution["paid_calls_authorized"]:
        raise Study1ContractError("draft contracts cannot authorize paid calls")
    if execution["contract_status"] == "draft" and source["normalized_material_sha256"] is not None:
        raise Study1ContractError("draft contract must not publish a frozen material hash")
    if execution["contract_status"] == "frozen":
        stored_hash = source["normalized_material_sha256"]
        if stored_hash is None:
            raise Study1ContractError("frozen contract must publish a material hash")
        if stored_hash != normalized_material_hash(contract):
            raise Study1ContractError("frozen material hash does not match contract")


def normalized_material_hash(contract: dict[str, Any]) -> str:
    payload = {
        "participant_role": contract["materials"]["participant_role"],
        "common_scenario": contract["materials"]["common_scenario"],
        "arms": contract["materials"]["arms"],
        "response_instruction": contract["materials"]["response_instruction"],
        "outcomes": contract["outcomes"],
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
