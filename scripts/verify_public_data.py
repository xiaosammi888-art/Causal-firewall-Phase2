#!/usr/bin/env python3
"""Verify the public Study 1 data manifest and basic safety invariants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/CF-S1-CONFIRMATORY"
MANIFEST = DATA / "release_manifest.json"


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for record in manifest["files"]:
        path = ROOT / record["path"]
        if not path.is_file():
            raise FileNotFoundError(record["path"])
        if path.stat().st_size != record["bytes"]:
            raise ValueError(f"size mismatch: {record['path']}")
        if sha256(path) != record["sha256"]:
            raise ValueError(f"hash mismatch: {record['path']}")

    data_path = DATA / "public_semantic_components.jsonl"
    rows = [json.loads(line) for line in data_path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) != manifest["rows"]:
        raise ValueError("row count mismatch")
    expected_fields = {
        "fixture_id", "contract_id", "source_paper", "architecture", "cue",
        "arm_id", "source_component_id", "microblock", "value", "value_scale",
    }
    if any(set(row) != expected_fields for row in rows):
        raise ValueError("public row schema mismatch")
    serialized = data_path.read_text(encoding="utf-8").lower()
    forbidden = ("hmac_key", "api_key", "sk-", "/users/", "onedrive")
    if any(token in serialized for token in forbidden):
        raise ValueError("forbidden private token in public data")
    print(f"public_data_verified=true rows={len(rows)} sha256={sha256(data_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
