"""Synthetic-only test harness for the Study 1 confirmatory analysis contract."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


ALLOWED_FIXTURE_CLASSIFICATION = "synthetic_test_fixture_no_mapping"
ALLOWED_REGISTRY_STATUSES = {
    "draft_blinded_not_frozen_no_analysis_or_unblinding_authority",
    "frozen_blinded_v0_2_no_analysis_or_unblinding_authority",
}
ARCHITECTURES = (
    "C_fresh_context_manual_whitelist",
    "D_labeled_causal_firewall",
)
CUES = ("aligned", "reversed")
ROW_FIELDS = {
    "fixture_id",
    "contract_id",
    "source_paper",
    "architecture",
    "cue",
    "arm_id",
    "source_component_id",
    "microblock",
    "value",
    "value_scale",
}
FORBIDDEN_PATH_TOKENS = ("restricted", "crosswalk", "unblinding", "unblind")


@dataclass(frozen=True)
class AnalysisSettings:
    primary_bootstrap_replicates: int = 20_000
    article_bootstrap_replicates: int = 20_000
    replication_bootstrap_replicates: int = 20_000
    primary_seed: int = 61_001
    article_seed: int = 61_002


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def ensure_safe_path(path: Path) -> None:
    lowered = str(path.resolve()).lower()
    if any(token in lowered for token in FORBIDDEN_PATH_TOKENS):
        raise ValueError("forbidden_mapping_or_unblinding_path")


def percentile(values: list[float], probability: float) -> float:
    if not values or not 0.0 <= probability <= 1.0:
        raise ValueError("invalid_percentile_request")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[lower_index]
    fraction = position - lower_index
    return ordered[lower_index] * (1.0 - fraction) + ordered[upper_index] * fraction


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    if not p_values or any(not 0.0 <= value <= 1.0 for value in p_values.values()):
        raise ValueError("invalid_holm_p_values")
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    adjusted: dict[str, float] = {}
    running_maximum = 0.0
    total = len(ordered)
    for rank, (identifier, raw_p_value) in enumerate(ordered):
        candidate = min(1.0, (total - rank) * raw_p_value)
        running_maximum = max(running_maximum, candidate)
        adjusted[identifier] = running_maximum
    return adjusted


def _beta_continued_fraction(a_value: float, b_value: float, x_value: float) -> float:
    maximum_iterations = 400
    epsilon = 3e-14
    minimum_float = 1e-300
    qab = a_value + b_value
    qap = a_value + 1.0
    qam = a_value - 1.0
    c_value = 1.0
    d_value = 1.0 - qab * x_value / qap
    if abs(d_value) < minimum_float:
        d_value = minimum_float
    d_value = 1.0 / d_value
    result = d_value
    for iteration in range(1, maximum_iterations + 1):
        doubled = 2 * iteration
        coefficient = (
            iteration
            * (b_value - iteration)
            * x_value
            / ((qam + doubled) * (a_value + doubled))
        )
        d_value = 1.0 + coefficient * d_value
        if abs(d_value) < minimum_float:
            d_value = minimum_float
        c_value = 1.0 + coefficient / c_value
        if abs(c_value) < minimum_float:
            c_value = minimum_float
        d_value = 1.0 / d_value
        result *= d_value * c_value
        coefficient = -(
            (a_value + iteration)
            * (qab + iteration)
            * x_value
            / ((a_value + doubled) * (qap + doubled))
        )
        d_value = 1.0 + coefficient * d_value
        if abs(d_value) < minimum_float:
            d_value = minimum_float
        c_value = 1.0 + coefficient / c_value
        if abs(c_value) < minimum_float:
            c_value = minimum_float
        d_value = 1.0 / d_value
        increment = d_value * c_value
        result *= increment
        if abs(increment - 1.0) <= epsilon:
            return result
    raise ArithmeticError("incomplete_beta_continued_fraction_did_not_converge")


def regularized_incomplete_beta(
    x_value: float, a_value: float, b_value: float
) -> float:
    if not 0.0 <= x_value <= 1.0 or a_value <= 0.0 or b_value <= 0.0:
        raise ValueError("invalid_regularized_incomplete_beta_request")
    if x_value in (0.0, 1.0):
        return x_value
    leading = math.exp(
        math.lgamma(a_value + b_value)
        - math.lgamma(a_value)
        - math.lgamma(b_value)
        + a_value * math.log(x_value)
        + b_value * math.log1p(-x_value)
    )
    threshold = (a_value + 1.0) / (a_value + b_value + 2.0)
    if x_value < threshold:
        return leading * _beta_continued_fraction(
            a_value, b_value, x_value
        ) / a_value
    return 1.0 - leading * _beta_continued_fraction(
        b_value, a_value, 1.0 - x_value
    ) / b_value


def student_t_cdf(value: float, degrees_of_freedom: float) -> float:
    if not math.isfinite(value) or degrees_of_freedom <= 0.0:
        raise ValueError("invalid_student_t_cdf_request")
    if value == 0.0:
        return 0.5
    beta_argument = degrees_of_freedom / (degrees_of_freedom + value * value)
    tail = 0.5 * regularized_incomplete_beta(
        beta_argument, degrees_of_freedom / 2.0, 0.5
    )
    return 1.0 - tail if value > 0.0 else tail


def student_t_quantile(probability: float, degrees_of_freedom: float) -> float:
    if not 0.0 < probability < 1.0 or degrees_of_freedom <= 0.0:
        raise ValueError("invalid_student_t_quantile_request")
    if probability == 0.5:
        return 0.0
    if probability < 0.5:
        return -student_t_quantile(1.0 - probability, degrees_of_freedom)
    lower_bound = 0.0
    upper_bound = 1.0
    while student_t_cdf(upper_bound, degrees_of_freedom) < probability:
        upper_bound *= 2.0
    for _ in range(100):
        midpoint = (lower_bound + upper_bound) / 2.0
        if student_t_cdf(midpoint, degrees_of_freedom) < probability:
            lower_bound = midpoint
        else:
            upper_bound = midpoint
    return (lower_bound + upper_bound) / 2.0


def load_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    ensure_safe_path(registry_path)
    registry = read_json(registry_path)
    if registry.get("status") not in ALLOWED_REGISTRY_STATUSES:
        raise ValueError("registry_status_not_allowed_for_synthetic_test")
    experiments = registry.get("experiments", [])
    if len(experiments) != 30:
        raise ValueError("registry_experiment_count_mismatch")
    if sum(len(experiment["components"]) for experiment in experiments) != 33:
        raise ValueError("registry_component_count_mismatch")
    if len({experiment["source_paper"] for experiment in experiments}) != 28:
        raise ValueError("registry_source_paper_cluster_count_mismatch")
    scope = registry.get("scope", {})
    if (
        scope.get("primary_experiments") != 30
        or scope.get("primary_components") != 33
        or scope.get("source_paper_clusters") != 28
        or tuple(scope.get("architectures", ())) != ARCHITECTURES
        or tuple(scope.get("cues", ())) != CUES
    ):
        raise ValueError("registry_scope_mismatch")
    blinding = registry.get("blinding_declaration", {})
    if (
        blinding.get("restricted_crosswalk_read") is not False
        or blinding.get("condition_mapping_used") is not False
        or blinding.get("effect_estimates_computed") is not False
        or blinding.get("p_values_computed") is not False
        or blinding.get("replication_judgments_computed") is not False
        or blinding.get("api_calls") != 0
    ):
        raise ValueError("registry_blinding_declaration_invalid")
    return registry


def _source_component_id(component: dict[str, Any]) -> str:
    return str(component.get("source_component_id", component["component_id"]))


def _decode_value(value: float, value_rule: str) -> float:
    if value_rule == "default_normalized_primary":
        return value
    if value_rule == "centered_difference_component":
        return 2.0 * value - 1.0
    if value_rule == "emotional_ambivalence_component":
        return 1.5 * value - 0.5
    if value_rule == "counteroffer_fraction_of_point_offer":
        return value / 100.0
    raise ValueError(f"unknown_component_value_rule:{value_rule}")


def _encode_value(analysis_value: float, value_rule: str) -> tuple[float, str]:
    if value_rule == "default_normalized_primary":
        value, scale = analysis_value, "normalized_0_1"
    elif value_rule == "centered_difference_component":
        value, scale = (analysis_value + 1.0) / 2.0, "normalized_0_1"
    elif value_rule == "emotional_ambivalence_component":
        value, scale = (analysis_value + 0.5) / 1.5, "normalized_0_1"
    elif value_rule == "counteroffer_fraction_of_point_offer":
        value, scale = analysis_value * 100.0, "raw_unbounded"
    else:
        raise ValueError(f"unknown_component_value_rule:{value_rule}")
    if scale == "normalized_0_1" and not 0.0 <= value <= 1.0:
        raise ValueError("synthetic_generator_value_out_of_range")
    return value, scale


def _stable_noise(identifier: str) -> float:
    integer = int(hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:16], 16)
    unit_value = integer / float(0xFFFFFFFFFFFFFFFF)
    return (2.0 * unit_value - 1.0) * 0.002


def _base_for_rule(value_rule: str) -> float:
    if value_rule == "default_normalized_primary":
        return 0.5
    if value_rule == "centered_difference_component":
        return 0.0
    if value_rule == "emotional_ambivalence_component":
        return 0.25
    if value_rule == "counteroffer_fraction_of_point_offer":
        return 1.0
    raise ValueError(f"unknown_component_value_rule:{value_rule}")


def _synthetic_specifications(
    registry: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    specifications: dict[tuple[str, str], dict[str, Any]] = {}
    for experiment in registry["experiments"]:
        component_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for component in experiment["components"]:
            component_groups[_source_component_id(component)].append(component)
        for source_component_id, components in component_groups.items():
            value_rules = {component["value_rule"] for component in components}
            if len(value_rules) != 1:
                raise ValueError("shared_source_component_has_multiple_value_rules")
            specifications[(experiment["contract_id"], source_component_id)] = {
                "value_rule": next(iter(value_rules)),
                "arm_signal": {
                    arm_id: sum(
                        float(component["benchmark_sign"])
                        * float(component["arm_weights"][arm_id])
                        for component in components
                    )
                    for arm_id in components[0]["arm_weights"]
                },
            }
    return specifications


def _expected_synthetic_value(
    contract_id: str,
    architecture: str,
    cue: str,
    arm_id: str,
    source_component_id: str,
    microblock: int,
    specification: dict[str, Any],
) -> tuple[float, str]:
    cue_multiplier = 0.0
    if architecture == ARCHITECTURES[0]:
        cue_multiplier = 0.04 if cue == "aligned" else -0.04
    noise_key = "|".join(
        (
            contract_id,
            architecture,
            cue,
            arm_id,
            source_component_id,
            str(microblock),
        )
    )
    analysis_value = (
        _base_for_rule(specification["value_rule"])
        + (0.03 + cue_multiplier) * specification["arm_signal"][arm_id]
        + _stable_noise(noise_key)
    )
    value, value_scale = _encode_value(analysis_value, specification["value_rule"])
    return round(value, 12), value_scale


def generate_synthetic_fixture(
    registry_path: str | Path,
    output_dir: str | Path,
    draws_per_cell: int = 8,
) -> Path:
    if draws_per_cell < 2:
        raise ValueError("synthetic_draws_per_cell_must_be_at_least_two")
    registry_file = Path(registry_path)
    fixture_dir = Path(output_dir)
    ensure_safe_path(registry_file)
    ensure_safe_path(fixture_dir)
    if fixture_dir.exists():
        raise FileExistsError("refusing_to_overwrite_synthetic_fixture")
    registry = load_registry(registry_file)
    fixture_id = f"CF-S1-SYNTHETIC-FIXTURE-{draws_per_cell}-DRAWS"
    rows: list[dict[str, Any]] = []
    synthetic_specifications = _synthetic_specifications(registry)

    for experiment in registry["experiments"]:
        source_component_ids = sorted(
            {
                _source_component_id(component)
                for component in experiment["components"]
            }
        )
        for source_component_id in source_component_ids:
            specification = synthetic_specifications[
                (experiment["contract_id"], source_component_id)
            ]
            for architecture in ARCHITECTURES:
                for cue in CUES:
                    for arm_id in sorted(specification["arm_signal"]):
                        for microblock in range(1, draws_per_cell + 1):
                            value, value_scale = _expected_synthetic_value(
                                experiment["contract_id"],
                                architecture,
                                cue,
                                arm_id,
                                source_component_id,
                                microblock,
                                specification,
                            )
                            rows.append(
                                {
                                    "fixture_id": fixture_id,
                                    "contract_id": experiment["contract_id"],
                                    "source_paper": experiment["source_paper"],
                                    "architecture": architecture,
                                    "cue": cue,
                                    "arm_id": arm_id,
                                    "source_component_id": source_component_id,
                                    "microblock": microblock,
                                    "value": value,
                                    "value_scale": value_scale,
                                }
                            )

    fixture_dir.mkdir(parents=True, exist_ok=False)
    data_path = fixture_dir / "semantic_components.jsonl"
    data_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    manifest = {
        "fixture_id": fixture_id,
        "format_version": "1.0.0",
        "classification": ALLOWED_FIXTURE_CLASSIFICATION,
        "status": "synthetic_only_nonconfirmatory",
        "registry": {
            "path": str(registry_file),
            "sha256": digest(registry_file),
        },
        "dataset": {
            "path": data_path.name,
            "sha256": digest(data_path),
            "rows": len(rows),
            "draws_per_cell": draws_per_cell,
        },
        "safety": {
            "mapping_used": False,
            "restricted_crosswalk_read": False,
            "real_confirmatory_data_used": False,
            "api_calls": 0,
            "network_calls": 0,
            "confirmatory_inference_authorized": False,
        },
    }
    manifest_path = fixture_dir / "fixture_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _expected_fixture_keys(
    registry: dict[str, Any], draws_per_cell: int
) -> set[tuple[str, str, str, str, str, int]]:
    expected: set[tuple[str, str, str, str, str, int]] = set()
    for experiment in registry["experiments"]:
        source_components = {
            _source_component_id(component) for component in experiment["components"]
        }
        arms = set(experiment["components"][0]["arm_weights"])
        for component in experiment["components"]:
            if set(component["arm_weights"]) != arms:
                raise ValueError("component_arm_set_mismatch")
        for architecture in ARCHITECTURES:
            for cue in CUES:
                for arm_id in arms:
                    for source_component_id in source_components:
                        for microblock in range(1, draws_per_cell + 1):
                            expected.add(
                                (
                                    experiment["contract_id"],
                                    architecture,
                                    cue,
                                    arm_id,
                                    source_component_id,
                                    microblock,
                                )
                            )
    return expected


def load_synthetic_fixture(
    fixture_dir: str | Path,
    registry_path: str | Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    fixture_path = Path(fixture_dir)
    registry_file = Path(registry_path)
    ensure_safe_path(fixture_path)
    ensure_safe_path(registry_file)
    registry = load_registry(registry_file)
    manifest = read_json(fixture_path / "fixture_manifest.json")
    if manifest.get("classification") != ALLOWED_FIXTURE_CLASSIFICATION:
        raise ValueError("fixture_classification_not_synthetic")
    if manifest.get("status") != "synthetic_only_nonconfirmatory":
        raise ValueError("fixture_status_not_synthetic_only")
    required_safety = {
        "mapping_used": False,
        "restricted_crosswalk_read": False,
        "real_confirmatory_data_used": False,
        "api_calls": 0,
        "network_calls": 0,
        "confirmatory_inference_authorized": False,
    }
    if manifest.get("safety") != required_safety:
        raise ValueError("fixture_safety_declaration_invalid")
    if manifest.get("registry", {}).get("sha256") != digest(registry_file):
        raise ValueError("fixture_registry_hash_mismatch")

    data_path = fixture_path / str(manifest["dataset"]["path"])
    ensure_safe_path(data_path)
    if digest(data_path) != manifest["dataset"]["sha256"]:
        raise ValueError("fixture_dataset_hash_mismatch")
    rows = read_jsonl(data_path)
    if len(rows) != int(manifest["dataset"]["rows"]):
        raise ValueError("fixture_dataset_row_count_mismatch")
    if any(set(row) != ROW_FIELDS for row in rows):
        raise ValueError("fixture_row_schema_mismatch")
    if any(row["fixture_id"] != manifest["fixture_id"] for row in rows):
        raise ValueError("fixture_id_mismatch")

    draws_per_cell = int(manifest["dataset"]["draws_per_cell"])
    expected_keys = _expected_fixture_keys(registry, draws_per_cell)
    actual_keys: set[tuple[str, str, str, str, str, int]] = set()
    experiment_lookup = {
        experiment["contract_id"]: experiment for experiment in registry["experiments"]
    }
    value_rule_lookup: dict[tuple[str, str], str] = {}
    for experiment in registry["experiments"]:
        for component in experiment["components"]:
            key = (experiment["contract_id"], _source_component_id(component))
            previous = value_rule_lookup.setdefault(key, component["value_rule"])
            if previous != component["value_rule"]:
                raise ValueError("shared_source_component_value_rule_mismatch")
    synthetic_specifications = _synthetic_specifications(registry)

    for row in rows:
        contract_id = str(row["contract_id"])
        if contract_id not in experiment_lookup:
            raise ValueError("fixture_unknown_contract")
        if row["source_paper"] != experiment_lookup[contract_id]["source_paper"]:
            raise ValueError("fixture_source_paper_mismatch")
        if row["architecture"] not in ARCHITECTURES or row["cue"] not in CUES:
            raise ValueError("fixture_condition_value_invalid")
        if not math.isfinite(float(row["value"])):
            raise ValueError("fixture_nonfinite_value")
        key = (
            contract_id,
            str(row["architecture"]),
            str(row["cue"]),
            str(row["arm_id"]),
            str(row["source_component_id"]),
            int(row["microblock"]),
        )
        if key in actual_keys:
            raise ValueError("fixture_duplicate_semantic_row")
        actual_keys.add(key)
        value_rule = value_rule_lookup[(contract_id, str(row["source_component_id"]))]
        expected_scale = (
            "raw_unbounded"
            if value_rule == "counteroffer_fraction_of_point_offer"
            else "normalized_0_1"
        )
        if row["value_scale"] != expected_scale:
            raise ValueError("fixture_value_scale_mismatch")
        if expected_scale == "normalized_0_1" and not 0.0 <= float(row["value"]) <= 1.0:
            raise ValueError("fixture_normalized_value_out_of_range")
        expected_value, deterministic_scale = _expected_synthetic_value(
            contract_id,
            str(row["architecture"]),
            str(row["cue"]),
            str(row["arm_id"]),
            str(row["source_component_id"]),
            int(row["microblock"]),
            synthetic_specifications[
                (contract_id, str(row["source_component_id"]))
            ],
        )
        if deterministic_scale != row["value_scale"] or not math.isclose(
            float(row["value"]), expected_value, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("fixture_value_not_deterministic_synthetic")

    if actual_keys != expected_keys:
        raise ValueError("fixture_cartesian_completeness_failure")
    return manifest, rows, registry


def _cell_means(
    rows: list[dict[str, Any]], registry: dict[str, Any]
) -> tuple[
    dict[tuple[str, str, str, str, str], float],
    dict[tuple[str, str, str, str, str, int], float],
]:
    value_rule_lookup = {
        (experiment["contract_id"], _source_component_id(component)): component[
            "value_rule"
        ]
        for experiment in registry["experiments"]
        for component in experiment["components"]
    }
    grouped: dict[tuple[str, str, str, str, str], list[float]] = defaultdict(list)
    decoded_rows: dict[tuple[str, str, str, str, str, int], float] = {}
    for row in rows:
        group_key = (
            str(row["contract_id"]),
            str(row["architecture"]),
            str(row["cue"]),
            str(row["arm_id"]),
            str(row["source_component_id"]),
        )
        value_rule = value_rule_lookup[(group_key[0], group_key[4])]
        decoded = _decode_value(float(row["value"]), value_rule)
        grouped[group_key].append(decoded)
        decoded_rows[(*group_key, int(row["microblock"]))] = decoded
    means = {key: statistics.fmean(values) for key, values in grouped.items()}
    return means, decoded_rows


def _component_delta(
    cell_means: dict[tuple[str, str, str, str, str], float],
    experiment: dict[str, Any],
    component: dict[str, Any],
    architecture: str,
    cue: str,
) -> float:
    source_component_id = _source_component_id(component)
    raw_contrast = sum(
        float(weight)
        * cell_means[
            (
                experiment["contract_id"],
                architecture,
                cue,
                arm_id,
                source_component_id,
            )
        ]
        for arm_id, weight in component["arm_weights"].items()
    )
    return float(component["benchmark_sign"]) * raw_contrast


def _primary_estimands(
    cell_means: dict[tuple[str, str, str, str, str], float],
    registry: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    experiment_results: list[dict[str, Any]] = []
    experiment_theta: dict[str, float] = {}
    for experiment in registry["experiments"]:
        component_results: list[dict[str, Any]] = []
        for component in experiment["components"]:
            deltas = {
                architecture: {
                    cue: _component_delta(
                        cell_means, experiment, component, architecture, cue
                    )
                    for cue in CUES
                }
                for architecture in ARCHITECTURES
            }
            gamma = {
                architecture: deltas[architecture]["aligned"]
                - deltas[architecture]["reversed"]
                for architecture in ARCHITECTURES
            }
            theta = gamma[ARCHITECTURES[0]] - gamma[ARCHITECTURES[1]]
            component_results.append(
                {
                    "component_id": component["component_id"],
                    "delta": deltas,
                    "gamma": gamma,
                    "theta": theta,
                }
            )
        theta_value = statistics.fmean(
            component_result["theta"] for component_result in component_results
        )
        experiment_theta[experiment["contract_id"]] = theta_value
        experiment_results.append(
            {
                "contract_id": experiment["contract_id"],
                "source_study_id": experiment["source_study_id"],
                "source_paper": experiment["source_paper"],
                "components": component_results,
                "theta": theta_value,
            }
        )
    return experiment_results, experiment_theta


def _microblock_experiment_estimands(
    decoded_rows: dict[tuple[str, str, str, str, str, int], float],
    registry: dict[str, Any],
    draws_per_cell: int,
) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {
        experiment["contract_id"]: [] for experiment in registry["experiments"]
    }
    for microblock in range(1, draws_per_cell + 1):
        microblock_cells = {
            key[:-1]: value
            for key, value in decoded_rows.items()
            if key[-1] == microblock
        }
        _, experiment_theta = _primary_estimands(microblock_cells, registry)
        for contract_id, theta_value in experiment_theta.items():
            values[contract_id].append(theta_value)
    return values


def _within_experiment_mc_variances(
    microblock_estimands: dict[str, list[float]],
) -> dict[str, float]:
    variances: dict[str, float] = {}
    for contract_id, estimates in microblock_estimands.items():
        if len(estimates) < 2:
            raise ValueError("within_experiment_mc_variance_requires_two_draws")
        variance = statistics.variance(estimates) / len(estimates)
        if not math.isfinite(variance) or variance <= 0.0:
            raise ValueError("within_experiment_mc_variance_not_positive")
        variances[contract_id] = variance
    return variances


def cr2_intercept_model(
    experiment_theta: dict[str, float],
    registry: dict[str, Any],
) -> dict[str, Any]:
    experiments = registry["experiments"]
    contract_ids = [experiment["contract_id"] for experiment in experiments]
    outcomes = np.asarray(
        [experiment_theta[contract_id] for contract_id in contract_ids], dtype=float
    )
    cluster_labels = [experiment["source_paper"] for experiment in experiments]
    sample_size = len(outcomes)
    estimate = float(np.mean(outcomes))
    residuals = outcomes - estimate
    variance_numerator = 0.0
    residual_maker = np.eye(sample_size) - np.ones((sample_size, sample_size)) / sample_size
    satterthwaite_matrix = np.zeros((sample_size, sample_size), dtype=float)
    for cluster_label in sorted(set(cluster_labels)):
        indices = np.asarray(
            [
                index
                for index, label in enumerate(cluster_labels)
                if label == cluster_label
            ],
            dtype=int,
        )
        cluster_size = len(indices)
        adjustment = 1.0 / math.sqrt(1.0 - cluster_size / sample_size)
        cluster_score = adjustment * float(np.sum(residuals[indices]))
        variance_numerator += cluster_score * cluster_score
        indicator = np.zeros(sample_size, dtype=float)
        indicator[indices] = 1.0
        loading = residual_maker @ (adjustment * indicator / sample_size)
        satterthwaite_matrix += np.outer(loading, loading)
    variance = variance_numerator / (sample_size * sample_size)
    if not math.isfinite(variance) or variance <= 0.0:
        raise ValueError("cr2_variance_not_positive")
    standard_error = math.sqrt(variance)
    trace_value = float(np.trace(satterthwaite_matrix))
    trace_square = float(np.trace(satterthwaite_matrix @ satterthwaite_matrix))
    degrees_of_freedom = trace_value * trace_value / trace_square
    statistic = estimate / standard_error
    p_value = 2.0 * (1.0 - student_t_cdf(abs(statistic), degrees_of_freedom))
    critical_value = student_t_quantile(0.975, degrees_of_freedom)
    return {
        "status": "executed_synthetic_only",
        "model": "intercept_only_ols",
        "cluster_variable": "source_paper",
        "clusters": len(set(cluster_labels)),
        "experiments": sample_size,
        "small_sample_adjustment": "CR2_identity_working_covariance",
        "degrees_of_freedom_method": "Satterthwaite_quadratic_form",
        "estimate": estimate,
        "standard_error": standard_error,
        "degrees_of_freedom": degrees_of_freedom,
        "t_statistic": statistic,
        "p_value_two_sided": p_value,
        "confidence_interval_95": [
            estimate - critical_value * standard_error,
            estimate + critical_value * standard_error,
        ],
    }


def _reml_objective(
    outcomes: np.ndarray,
    within_variances: np.ndarray,
    paper_design: np.ndarray,
    paper_variance: float,
    experiment_variance: float,
) -> tuple[float, dict[str, float]]:
    covariance = (
        np.diag(within_variances + experiment_variance)
        + paper_variance * (paper_design @ paper_design.T)
    )
    sign, log_determinant = np.linalg.slogdet(covariance)
    if sign <= 0.0 or not math.isfinite(float(log_determinant)):
        return math.inf, {}
    intercept = np.ones(len(outcomes), dtype=float)
    try:
        inverse_outcomes = np.linalg.solve(covariance, outcomes)
        inverse_intercept = np.linalg.solve(covariance, intercept)
    except np.linalg.LinAlgError:
        return math.inf, {}
    information = float(intercept @ inverse_intercept)
    if information <= 0.0 or not math.isfinite(information):
        return math.inf, {}
    estimate = float(intercept @ inverse_outcomes / information)
    residuals = outcomes - estimate
    quadratic = float(residuals @ np.linalg.solve(covariance, residuals))
    objective = 0.5 * (
        float(log_determinant)
        + math.log(information)
        + quadratic
        + (len(outcomes) - 1) * math.log(2.0 * math.pi)
    )
    return objective, {
        "estimate": estimate,
        "information": information,
        "quadratic": quadratic,
    }


def _fit_reml_variance_components(
    outcomes: np.ndarray,
    within_variances: np.ndarray,
    paper_design: np.ndarray,
) -> tuple[float, float, float, dict[str, float], int]:
    observed_variance = float(np.var(outcomes, ddof=1))
    upper_bound = max(observed_variance, float(np.max(within_variances)), 1e-8) * 20.0
    evaluations = 0

    def evaluate(parameters: tuple[float, float]) -> tuple[float, dict[str, float]]:
        nonlocal evaluations
        evaluations += 1
        return _reml_objective(
            outcomes,
            within_variances,
            paper_design,
            parameters[0],
            parameters[1],
        )

    best_parameters = (0.0, 0.0)
    best_objective, best_details = evaluate(best_parameters)
    for _ in range(4):
        grid = [upper_bound * (index / 24.0) ** 4 for index in range(25)]
        candidates: list[tuple[float, float, float, dict[str, float]]] = []
        for paper_variance in grid:
            for experiment_variance in grid:
                objective, details = evaluate((paper_variance, experiment_variance))
                candidates.append(
                    (objective, paper_variance, experiment_variance, details)
                )
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        for _, start_paper, start_experiment, _ in candidates[:8]:
            parameters = np.asarray([start_paper, start_experiment], dtype=float)
            steps = np.asarray([upper_bound / 8.0, upper_bound / 8.0], dtype=float)
            objective, details = evaluate((float(parameters[0]), float(parameters[1])))
            for _ in range(160):
                trial_rows: list[
                    tuple[float, float, float, np.ndarray, dict[str, float]]
                ] = []
                for paper_direction in (-1.0, 0.0, 1.0):
                    for experiment_direction in (-1.0, 0.0, 1.0):
                        if paper_direction == 0.0 and experiment_direction == 0.0:
                            continue
                        trial = np.clip(
                            parameters
                            + steps
                            * np.asarray(
                                [paper_direction, experiment_direction], dtype=float
                            ),
                            0.0,
                            upper_bound,
                        )
                        trial_objective, trial_details = evaluate(
                            (float(trial[0]), float(trial[1]))
                        )
                        trial_rows.append(
                            (
                                trial_objective,
                                float(trial[0]),
                                float(trial[1]),
                                trial,
                                trial_details,
                            )
                        )
                trial_rows.sort(key=lambda item: (item[0], item[1], item[2]))
                trial_objective, _, _, trial, trial_details = trial_rows[0]
                if trial_objective < objective - 1e-13:
                    parameters = trial
                    objective = trial_objective
                    details = trial_details
                else:
                    steps /= 2.0
                if float(np.max(steps)) <= max(upper_bound * 1e-11, 1e-14):
                    break
            if objective < best_objective:
                best_objective = objective
                best_parameters = (float(parameters[0]), float(parameters[1]))
                best_details = details
        if max(best_parameters) < 0.95 * upper_bound:
            break
        upper_bound *= 4.0
    if not best_details or not math.isfinite(best_objective):
        raise ArithmeticError("reml_optimizer_failed")
    if max(best_parameters) >= 0.95 * upper_bound:
        raise ArithmeticError("reml_optimizer_upper_boundary")
    return (
        best_parameters[0],
        best_parameters[1],
        best_objective,
        best_details,
        evaluations,
    )


def reml_multilevel_meta_analysis(
    experiment_theta: dict[str, float],
    within_experiment_variances: dict[str, float],
    registry: dict[str, Any],
) -> dict[str, Any]:
    experiments = registry["experiments"]
    contract_ids = [experiment["contract_id"] for experiment in experiments]
    outcomes = np.asarray(
        [experiment_theta[contract_id] for contract_id in contract_ids], dtype=float
    )
    within_variances = np.asarray(
        [within_experiment_variances[contract_id] for contract_id in contract_ids],
        dtype=float,
    )
    if np.any(~np.isfinite(within_variances)) or np.any(within_variances <= 0.0):
        raise ValueError("reml_within_experiment_variance_not_positive")
    papers = sorted({experiment["source_paper"] for experiment in experiments})
    paper_index = {paper: index for index, paper in enumerate(papers)}
    paper_design = np.zeros((len(experiments), len(papers)), dtype=float)
    for row_index, experiment in enumerate(experiments):
        paper_design[row_index, paper_index[experiment["source_paper"]]] = 1.0
    (
        paper_variance,
        experiment_variance,
        objective,
        details,
        evaluations,
    ) = _fit_reml_variance_components(outcomes, within_variances, paper_design)
    degrees_of_freedom = len(outcomes) - 1
    knapp_hartung_scale = details["quadratic"] / degrees_of_freedom
    standard_error = math.sqrt(knapp_hartung_scale / details["information"])
    if not math.isfinite(standard_error) or standard_error <= 0.0:
        raise ValueError("reml_knapp_hartung_standard_error_not_positive")
    critical_value = student_t_quantile(0.975, degrees_of_freedom)
    statistic = details["estimate"] / standard_error
    p_value = 2.0 * (1.0 - student_t_cdf(abs(statistic), degrees_of_freedom))
    return {
        "status": "executed_synthetic_only",
        "model": "intercept_plus_source_paper_random_intercept_plus_experiment_heterogeneity",
        "estimation": "REML",
        "optimizer": "deterministic_quartic_grid_multistart_pattern_search",
        "optimizer_evaluations": evaluations,
        "restricted_negative_log_likelihood": objective,
        "experiments": len(outcomes),
        "source_paper_clusters": len(papers),
        "paper_random_intercept_variance": paper_variance,
        "experiment_heterogeneity_variance": experiment_variance,
        "within_experiment_variance_source": "paired_microblock_theta_sample_variance_divided_by_draw_count",
        "estimate": details["estimate"],
        "knapp_hartung_scale": knapp_hartung_scale,
        "knapp_hartung_modified": False,
        "standard_error": standard_error,
        "degrees_of_freedom": degrees_of_freedom,
        "t_statistic": statistic,
        "p_value_two_sided": p_value,
        "confidence_interval_95": [
            details["estimate"] - critical_value * standard_error,
            details["estimate"] + critical_value * standard_error,
        ],
    }


def _cluster_bootstrap(
    experiment_theta: dict[str, float],
    registry: dict[str, Any],
    replicates: int,
    seed: int,
    article_equal: bool,
) -> list[float]:
    if replicates < 2:
        raise ValueError("bootstrap_replicates_must_be_at_least_two")
    paper_experiments: dict[str, list[str]] = defaultdict(list)
    for experiment in registry["experiments"]:
        paper_experiments[experiment["source_paper"]].append(experiment["contract_id"])
    papers = sorted(paper_experiments)
    random_generator = random.Random(seed)
    bootstrap_values: list[float] = []
    for _ in range(replicates):
        sampled_papers = [random_generator.choice(papers) for _ in papers]
        if article_equal:
            article_values = [
                statistics.fmean(
                    experiment_theta[contract_id]
                    for contract_id in paper_experiments[paper]
                )
                for paper in sampled_papers
            ]
            bootstrap_values.append(statistics.fmean(article_values))
        else:
            experiment_values = [
                experiment_theta[contract_id]
                for paper in sampled_papers
                for contract_id in paper_experiments[paper]
            ]
            bootstrap_values.append(statistics.fmean(experiment_values))
    return bootstrap_values


def _bootstrap_summary(
    point_estimate: float,
    bootstrap_values: list[float],
    one_sided: bool,
) -> dict[str, Any]:
    if one_sided:
        exceedances = sum(
            value - point_estimate >= point_estimate for value in bootstrap_values
        )
        p_value = (1 + exceedances) / (len(bootstrap_values) + 1)
    else:
        exceedances = sum(
            abs(value - point_estimate) >= abs(point_estimate)
            for value in bootstrap_values
        )
        p_value = (1 + exceedances) / (len(bootstrap_values) + 1)
    return {
        "estimate": point_estimate,
        "standard_error": statistics.stdev(bootstrap_values),
        "confidence_interval_95": [
            percentile(bootstrap_values, 0.025),
            percentile(bootstrap_values, 0.975),
        ],
        "p_value": p_value,
        "bootstrap_replicates": len(bootstrap_values),
    }


def _replication_seed(contract_id: str, component_id: str) -> int:
    value = f"CF-S1-REPLICATION|{contract_id}|{component_id}"
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def _replication_results(
    decoded_rows: dict[tuple[str, str, str, str, str, int], float],
    registry: dict[str, Any],
    draws_per_cell: int,
    bootstrap_replicates: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    component_results: list[dict[str, Any]] = []
    raw_p_values: dict[str, float] = {}
    for experiment in registry["experiments"]:
        for component in experiment["components"]:
            source_component_id = _source_component_id(component)
            microblock_effects: list[float] = []
            for microblock in range(1, draws_per_cell + 1):
                cue_effects: list[float] = []
                for cue in CUES:
                    raw_contrast = sum(
                        float(weight)
                        * decoded_rows[
                            (
                                experiment["contract_id"],
                                ARCHITECTURES[1],
                                cue,
                                arm_id,
                                source_component_id,
                                microblock,
                            )
                        ]
                        for arm_id, weight in component["arm_weights"].items()
                    )
                    cue_effects.append(
                        float(component["benchmark_sign"]) * raw_contrast
                    )
                microblock_effects.append(statistics.fmean(cue_effects))
            point_estimate = statistics.fmean(microblock_effects)
            random_generator = random.Random(
                _replication_seed(experiment["contract_id"], component["component_id"])
            )
            bootstrap_values = [
                statistics.fmean(
                    random_generator.choice(microblock_effects)
                    for _ in microblock_effects
                )
                for _ in range(bootstrap_replicates)
            ]
            summary = _bootstrap_summary(point_estimate, bootstrap_values, False)
            identifier = f"{experiment['contract_id']}:{component['component_id']}"
            raw_p_values[identifier] = summary["p_value"]
            component_results.append(
                {
                    "identifier": identifier,
                    "contract_id": experiment["contract_id"],
                    "component_id": component["component_id"],
                    "source_paper": experiment["source_paper"],
                    **summary,
                }
            )

    adjusted_p_values = holm_adjust(raw_p_values)
    for result in component_results:
        adjusted = adjusted_p_values[result["identifier"]]
        result["holm_adjusted_p_value"] = adjusted
        if result["estimate"] > 0.0 and adjusted < 0.05:
            result["label"] = "SUCCESS"
        elif result["estimate"] < 0.0 and adjusted < 0.05:
            result["label"] = "FAILURE"
        else:
            result["label"] = "INDETERMINATE"

    components_by_experiment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in component_results:
        components_by_experiment[result["contract_id"]].append(result)
    experiment_results: list[dict[str, Any]] = []
    for experiment in registry["experiments"]:
        labels = [
            result["label"] for result in components_by_experiment[experiment["contract_id"]]
        ]
        if all(label == "SUCCESS" for label in labels):
            label = "SUCCESS"
        elif any(component_label == "FAILURE" for component_label in labels):
            label = "FAILURE"
        else:
            label = "INDETERMINATE"
        experiment_results.append(
            {
                "contract_id": experiment["contract_id"],
                "source_study_id": experiment["source_study_id"],
                "source_paper": experiment["source_paper"],
                "component_labels": labels,
                "label": label,
            }
        )
    return component_results, experiment_results


def analyze_synthetic_fixture(
    fixture_dir: str | Path,
    registry_path: str | Path,
    output_dir: str | Path,
    settings: AnalysisSettings | None = None,
) -> tuple[Path, Path]:
    fixture_path = Path(fixture_dir)
    registry_file = Path(registry_path)
    analysis_dir = Path(output_dir)
    ensure_safe_path(fixture_path)
    ensure_safe_path(registry_file)
    ensure_safe_path(analysis_dir)
    if analysis_dir.exists():
        raise FileExistsError("refusing_to_overwrite_synthetic_analysis")
    analysis_settings = settings or AnalysisSettings()
    if min(
        analysis_settings.primary_bootstrap_replicates,
        analysis_settings.article_bootstrap_replicates,
        analysis_settings.replication_bootstrap_replicates,
    ) < 2:
        raise ValueError("analysis_bootstrap_replicates_must_be_at_least_two")

    manifest, rows, registry = load_synthetic_fixture(fixture_path, registry_file)
    cell_means, decoded_rows = _cell_means(rows, registry)
    experiment_results, experiment_theta = _primary_estimands(cell_means, registry)
    primary_estimate = statistics.fmean(experiment_theta.values())
    primary_bootstrap = _cluster_bootstrap(
        experiment_theta,
        registry,
        analysis_settings.primary_bootstrap_replicates,
        analysis_settings.primary_seed,
        False,
    )
    primary_result = _bootstrap_summary(primary_estimate, primary_bootstrap, True)
    primary_result["decision"] = (
        "REJECT_H0" if primary_result["p_value"] < 0.05 else "DO_NOT_REJECT_H0"
    )

    paper_experiments: dict[str, list[str]] = defaultdict(list)
    for experiment in registry["experiments"]:
        paper_experiments[experiment["source_paper"]].append(experiment["contract_id"])
    article_equal_estimate = statistics.fmean(
        statistics.fmean(experiment_theta[contract_id] for contract_id in contracts)
        for contracts in paper_experiments.values()
    )
    article_bootstrap = _cluster_bootstrap(
        experiment_theta,
        registry,
        analysis_settings.article_bootstrap_replicates,
        analysis_settings.article_seed,
        True,
    )
    article_result = _bootstrap_summary(
        article_equal_estimate, article_bootstrap, True
    )

    draws_per_cell = int(manifest["dataset"]["draws_per_cell"])
    microblock_estimands = _microblock_experiment_estimands(
        decoded_rows, registry, draws_per_cell
    )
    within_experiment_variances = _within_experiment_mc_variances(
        microblock_estimands
    )
    cr2_result = cr2_intercept_model(experiment_theta, registry)
    reml_result = reml_multilevel_meta_analysis(
        experiment_theta, within_experiment_variances, registry
    )
    replication_components, replication_experiments = _replication_results(
        decoded_rows,
        registry,
        draws_per_cell,
        analysis_settings.replication_bootstrap_replicates,
    )
    results = {
        "analysis_id": f"{manifest['fixture_id']}-ANALYSIS",
        "status": "synthetic_fixture_only_nonconfirmatory",
        "authority": {
            "confirmatory_analysis_authorized": False,
            "unblinding_authorized": False,
            "real_data_execution_authorized": False,
        },
        "blinding": {
            "mapping_used": False,
            "restricted_crosswalk_read": False,
            "condition_mapping_file_supported": False,
        },
        "inputs": {
            "fixture_manifest_sha256": digest(fixture_path / "fixture_manifest.json"),
            "fixture_dataset_sha256": manifest["dataset"]["sha256"],
            "registry_sha256": digest(registry_file),
        },
        "settings": {
            "draws_per_cell": draws_per_cell,
            "primary_bootstrap_replicates": analysis_settings.primary_bootstrap_replicates,
            "article_bootstrap_replicates": analysis_settings.article_bootstrap_replicates,
            "replication_bootstrap_replicates": analysis_settings.replication_bootstrap_replicates,
            "primary_seed": analysis_settings.primary_seed,
            "article_seed": analysis_settings.article_seed,
        },
        "primary_h2": primary_result,
        "experiment_estimands": experiment_results,
        "sensitivity": {
            "article_equal_mean": article_result,
            "cr2": cr2_result,
            "reml_multilevel_meta_analysis": reml_result,
            "within_experiment_mc_variances": [
                {
                    "contract_id": contract_id,
                    "variance": within_experiment_variances[contract_id],
                }
                for contract_id in sorted(within_experiment_variances)
            ],
        },
        "replication_diagnostics": {
            "multiplicity": "Holm FWER 0.05 across 33 registered components",
            "components": replication_components,
            "experiments": replication_experiments,
        },
        "execution": {
            "api_calls": 0,
            "network_calls": 0,
            "real_confirmatory_rows_read": 0,
        },
    }

    analysis_dir.mkdir(parents=True, exist_ok=False)
    results_path = analysis_dir / "synthetic_analysis_results.json"
    results_path.write_text(
        json.dumps(results, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    audit = {
        "status": "pass_synthetic_only_analysis_harness",
        "fixture_classification": manifest["classification"],
        "registry_experiments": len(registry["experiments"]),
        "registry_components": sum(
            len(experiment["components"]) for experiment in registry["experiments"]
        ),
        "registry_source_paper_clusters": len(
            {experiment["source_paper"] for experiment in registry["experiments"]}
        ),
        "fixture_rows": len(rows),
        "semantic_cells": len(cell_means),
        "mapping_used": False,
        "restricted_crosswalk_read": False,
        "api_calls": 0,
        "network_calls": 0,
        "results_sha256": digest(results_path),
    }
    audit_path = analysis_dir / "synthetic_analysis_audit.json"
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return results_path, audit_path
