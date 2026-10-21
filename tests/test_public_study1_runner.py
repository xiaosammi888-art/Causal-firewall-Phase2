from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from causal_firewall.study1_confirmatory_runner import run_confirmatory_offline_runner


ROOT = Path(__file__).resolve().parents[1]


class PublicStudy1RunnerTests(unittest.TestCase):
    def test_one_frozen_batch_compiles_without_network(self):
        manifest = ROOT / "experiments/study1/confirmatory_frozen_batch01/freeze_manifest.json"
        policy = ROOT / "experiments/study1/access_policy.json"
        with tempfile.TemporaryDirectory() as temporary:
            output = run_confirmatory_offline_runner(ROOT, manifest, policy, Path(temporary))
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["status"], "offline_test_pass")
            self.assertEqual(summary["contracts"], 8)
            self.assertEqual(summary["request_templates"], 72)
            self.assertEqual(summary["network_calls"], 0)
            self.assertFalse(summary["model_called"])
            self.assertFalse(summary["api_calls_authorized"])


if __name__ == "__main__":
    unittest.main()
