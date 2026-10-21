from __future__ import annotations

import json
import unittest
from pathlib import Path

from causal_firewall import study1_confirmatory_analysis_blinded as analysis


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/CF-S1-CONFIRMATORY/public_semantic_components.jsonl"
REGISTRY = ROOT / "experiments/study1/confirmatory_analysis_frozen_v0_2/blinded_estimand_registry_v0_2.json"


class PublicStudy1AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = analysis.load_registry(REGISTRY)
        cls.rows = analysis.read_jsonl(DATA)

    def test_public_dataset_is_complete(self):
        self.assertEqual(len(self.rows), 39_600)
        keys = {
            (row["contract_id"], row["architecture"], row["cue"], row["arm_id"], row["source_component_id"], int(row["microblock"]))
            for row in self.rows
        }
        self.assertEqual(keys, analysis._expected_fixture_keys(self.registry, 100))

    def test_unbootstrapped_primary_estimate_matches_release(self):
        means, _ = analysis._cell_means(self.rows, self.registry)
        _, theta = analysis._primary_estimands(means, self.registry)
        expected = json.loads((ROOT / "data/CF-S1-CONFIRMATORY/expected_confirmatory_analysis_results.json").read_text())
        self.assertAlmostEqual(sum(theta.values()) / len(theta), expected["primary_h2"]["estimate"], places=14)

    def test_registry_scope_is_frozen(self):
        self.assertEqual(len(self.registry["experiments"]), 30)
        self.assertEqual(sum(len(item["components"]) for item in self.registry["experiments"]), 33)
        self.assertEqual(len({item["source_paper"] for item in self.registry["experiments"]}), 28)


if __name__ == "__main__":
    unittest.main()
