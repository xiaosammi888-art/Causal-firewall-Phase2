from __future__ import annotations

import json
import unittest
from pathlib import Path

from causal_firewall.study1_contract import load_contract, normalized_material_hash


ROOT = Path(__file__).resolve().parents[1]


class PublicStudy1ContractTests(unittest.TestCase):
    def test_all_forty_contracts_are_frozen_and_hash_valid(self):
        paths = sorted((ROOT / "experiments/study1").glob("confirmatory_frozen_batch*/CF-S1-CONF-*/experiment_contract.json"))
        self.assertEqual(len(paths), 40)
        identifiers = set()
        for path in paths:
            contract = load_contract(path)
            identifiers.add(contract["identity"]["study_id"])
            self.assertEqual(contract["execution"]["contract_status"], "frozen")
            self.assertFalse(contract["execution"]["paid_calls_authorized"])
            self.assertEqual(contract["source"]["normalized_material_sha256"], normalized_material_hash(contract))
        self.assertEqual(len(identifiers), 40)

    def test_five_freeze_manifests_disable_calls(self):
        manifests = sorted((ROOT / "experiments/study1").glob("confirmatory_frozen_batch*/freeze_manifest.json"))
        self.assertEqual(len(manifests), 5)
        self.assertEqual(sum(len(json.loads(path.read_text())["contracts"]) for path in manifests), 40)
        for path in manifests:
            manifest = json.loads(path.read_text())
            self.assertTrue(manifest["contracts_frozen"])
            self.assertFalse(manifest["api_calls_authorized"])
            self.assertFalse(manifest["paid_calls_authorized"])
            self.assertEqual(manifest["network_calls_during_freeze"], 0)


if __name__ == "__main__":
    unittest.main()
