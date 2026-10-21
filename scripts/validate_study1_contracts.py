#!/usr/bin/env python3
"""Validate every frozen Study 1 confirmatory contract."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from causal_firewall.study1_contract import load_contract


def main() -> int:
    contract_paths = sorted(
        (ROOT / "experiments/study1").glob(
            "confirmatory_frozen_batch*/CF-S1-CONF-*/experiment_contract.json"
        )
    )
    if len(contract_paths) != 40:
        raise ValueError(f"expected 40 frozen contracts, found {len(contract_paths)}")
    identifiers = []
    for path in contract_paths:
        contract = load_contract(path)
        identifiers.append(contract["identity"]["study_id"])
        if contract["execution"]["contract_status"] != "frozen":
            raise ValueError(f"contract is not frozen: {path}")
        if contract["execution"]["paid_calls_authorized"] is not False:
            raise ValueError(f"paid calls enabled: {path}")
    if len(set(identifiers)) != 40:
        raise ValueError("duplicate contract identifier")
    print(f"contracts_validated={len(contract_paths)} unique_identifiers={len(set(identifiers))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
