from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from causal_firewall.io import load_policy
from causal_firewall.study1_contract import load_contract, validate_contract
from scripts.audit_new_experiment import audit


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/new_experiment_template/completed_example/experiment_contract.json"
TEMPLATE = ROOT / "examples/new_experiment_template/experiment_contract.template.json"
POLICY = ROOT / "examples/new_experiment_template/access_policy.template.json"


class NewExperimentTemplateTests(unittest.TestCase):
    def test_blank_scaffold_and_policy_are_structurally_valid(self):
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        validate_contract(template)
        policy = load_policy(POLICY)
        self.assertEqual(policy["default"], "deny")
        self.assertEqual(policy["derivation"]["inheritance"], "most_restrictive")

    def test_completed_example_is_frozen_and_hash_valid(self):
        contract = load_contract(EXAMPLE)
        self.assertEqual(contract["execution"]["contract_status"], "frozen")
        self.assertFalse(contract["execution"]["paid_calls_authorized"])

    def test_example_audit_demonstrates_the_cue_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = audit(EXAMPLE, POLICY, Path(temporary))
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["request_templates"], 8)
            self.assertTrue(summary["cue_boundary"]["manual_whitelist_admits_summary_context"])
            self.assertTrue(summary["cue_boundary"]["causal_firewall_denies_summary_context"])
            self.assertEqual(summary["network_calls"], 0)
            self.assertFalse(summary["model_called"])


if __name__ == "__main__":
    unittest.main()
