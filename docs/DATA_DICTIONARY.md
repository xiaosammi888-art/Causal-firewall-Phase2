# Public Semantic Data Dictionary

`data/CF-S1-CONFIRMATORY/public_semantic_components.jsonl` contains one JSON object per analysis component row.

| Field | Meaning |
|---|---|
| `fixture_id` | Public release identifier; constant across rows. |
| `contract_id` | Frozen Study 1 experiment contract identifier. |
| `source_paper` | Deidentified source-paper cluster identifier used for clustered inference. |
| `architecture` | `C_fresh_context_manual_whitelist` or `D_labeled_causal_firewall`. |
| `cue` | Hidden research-expectation cue direction: `aligned` or `reversed`. |
| `arm_id` | Experimental arm identifier defined in the frozen contract. |
| `source_component_id` | Outcome component used by the frozen estimand registry. |
| `microblock` | Paired replicate index from 1 through 100. |
| `value` | Numeric component value after deterministic outcome encoding but before the registry's analysis-scale transformation. |
| `value_scale` | `normalized_0_1` or `raw_unbounded`. |

The file has 39,600 rows and represents 38,400 logical response units. It contains no raw response text, participant personal data, API credentials, provider request identifiers, opaque HMAC codes, or HMAC key.
