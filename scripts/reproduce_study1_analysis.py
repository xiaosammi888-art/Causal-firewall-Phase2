#!/usr/bin/env python3
"""Recompute the frozen Study 1 analysis from public semantic data."""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from causal_firewall import study1_confirmatory_analysis_blinded as analysis


DATA = ROOT / "data/CF-S1-CONFIRMATORY/public_semantic_components.jsonl"
EXPECTED = ROOT / "data/CF-S1-CONFIRMATORY/expected_confirmatory_analysis_results.json"
REGISTRY = ROOT / "experiments/study1/confirmatory_analysis_frozen_v0_2/blinded_estimand_registry_v0_2.json"
OUTPUT = ROOT / "reproduction_outputs/analysis/reproduced_confirmatory_analysis.json"


def load_public_rows(registry: dict) -> list[dict]:
    rows = analysis.read_jsonl(DATA)
    if len(rows) != 39_600:
        raise ValueError("public analysis row count mismatch")
    if any(set(row) != analysis.ROW_FIELDS for row in rows):
        raise ValueError("public analysis row schema mismatch")
    expected_keys = analysis._expected_fixture_keys(registry, 100)
    actual_keys = {
        (
            row["contract_id"], row["architecture"], row["cue"], row["arm_id"],
            row["source_component_id"], int(row["microblock"]),
        )
        for row in rows
    }
    if actual_keys != expected_keys or len(actual_keys) != len(rows):
        raise ValueError("public semantic cartesian completeness failure")
    return rows


def compute() -> dict:
    registry = analysis.load_registry(REGISTRY)
    rows = load_public_rows(registry)
    settings = analysis.AnalysisSettings()
    cell_means, decoded_rows = analysis._cell_means(rows, registry)
    experiment_results, experiment_theta = analysis._primary_estimands(cell_means, registry)

    primary_estimate = statistics.fmean(experiment_theta.values())
    primary_result = analysis._bootstrap_summary(
        primary_estimate,
        analysis._cluster_bootstrap(
            experiment_theta, registry, settings.primary_bootstrap_replicates,
            settings.primary_seed, False,
        ),
        True,
    )
    primary_result["decision"] = "REJECT_H0" if primary_result["p_value"] < 0.05 else "DO_NOT_REJECT_H0"

    paper_experiments = defaultdict(list)
    for experiment in registry["experiments"]:
        paper_experiments[experiment["source_paper"]].append(experiment["contract_id"])
    article_estimate = statistics.fmean(
        statistics.fmean(experiment_theta[contract_id] for contract_id in contracts)
        for contracts in paper_experiments.values()
    )
    article_result = analysis._bootstrap_summary(
        article_estimate,
        analysis._cluster_bootstrap(
            experiment_theta, registry, settings.article_bootstrap_replicates,
            settings.article_seed, True,
        ),
        True,
    )
    microblock_estimands = analysis._microblock_experiment_estimands(decoded_rows, registry, 100)
    within_variances = analysis._within_experiment_mc_variances(microblock_estimands)
    components, experiments = analysis._replication_results(
        decoded_rows, registry, 100, settings.replication_bootstrap_replicates
    )
    return {
        "settings": {
            "draws_per_cell": 100,
            "primary_bootstrap_replicates": settings.primary_bootstrap_replicates,
            "article_bootstrap_replicates": settings.article_bootstrap_replicates,
            "replication_bootstrap_replicates": settings.replication_bootstrap_replicates,
            "primary_seed": settings.primary_seed,
            "article_seed": settings.article_seed,
        },
        "primary_h2": primary_result,
        "experiment_estimands": experiment_results,
        "sensitivity": {
            "article_equal_mean": article_result,
            "cr2": analysis.cr2_intercept_model(experiment_theta, registry),
            "reml_multilevel_meta_analysis": analysis.reml_multilevel_meta_analysis(
                experiment_theta, within_variances, registry
            ),
            "within_experiment_mc_variances": [
                {"contract_id": contract_id, "variance": within_variances[contract_id]}
                for contract_id in sorted(within_variances)
            ],
        },
        "replication_diagnostics": {
            "multiplicity": "Holm FWER 0.05 across 33 registered components",
            "components": components,
            "experiments": experiments,
        },
    }


def main() -> int:
    reproduced = compute()
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    sections = ("settings", "primary_h2", "experiment_estimands", "sensitivity", "replication_diagnostics")
    mismatches = [name for name in sections if reproduced[name] != expected[name]]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(reproduced, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if mismatches:
        raise ValueError(f"analysis mismatch in sections: {mismatches}")
    print(
        "exact_analysis_match=true "
        f"estimate={reproduced['primary_h2']['estimate']:.12f} "
        f"p={reproduced['primary_h2']['p_value']:.12g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
