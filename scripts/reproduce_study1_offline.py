#!/usr/bin/env python3
"""Run the complete public Study 1 offline reproduction."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    command = [sys.executable, *arguments]
    print("Running:", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("scripts/verify_public_data.py")
    run("-m", "unittest", "discover", "-s", "tests", "-v")
    run("scripts/validate_study1_contracts.py")
    run("scripts/audit_new_experiment.py")
    run("scripts/run_study1_contract_audit.py")
    run("scripts/reproduce_study1_analysis.py")
    print("All Study 1 offline reproduction gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
