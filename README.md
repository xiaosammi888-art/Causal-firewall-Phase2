# Causal-firewall-Phase2

This repository contains the public, offline reproducibility package for phase 2 of the Causal Firewall project. Phase 2 scales provenance-aware information-flow control across 30 confirmatory experiments drawn from 28 management and psychology source papers. (Note: Study1 in the file name corresponds to phase 2)

The public package supports two distinct checks:

1. **Infrastructure reproduction:** validate 40 frozen contracts (30 primary plus 10 prespecified expansion contracts) and compile provider-shaped requests without credentials, networking, or API calls.
2. **Statistical reproduction:** recompute the confirmatory estimate, sensitivity analyses, and replication diagnostics from 39,600 deidentified semantic component rows.

The primary result is an experiment-level mean firewall contrast of 0.0999 (SE 0.0267, 95% CI [0.0480, 0.1531], one-sided p = 0.00025). In operational terms, changing the direction of the hidden hypothesis moved the estimated treatment effect by approximately 0.10 more coded effect units under the manual-whitelist architecture than under the provenance-aware firewall. This result supports the central claim that field-name filtering alone is insufficient and that provenance-aware enforcement reduces the influence of restricted research expectations on simulated treatment effects.

## Reuse in a new experiment

| Question | Answer |
|---|---|
| **What do I provide?** | An experiment contract containing the population, arms, participant-visible materials, outcomes, and restricted research expectations, plus a deny-by-default access policy. |
| **What do I run?** | `python3 scripts/audit_new_experiment.py` for the completed example, or pass `--contract` and `--policy` for your own study. |
| **What do I get?** | Validated contracts, field-level allow/deny decisions, inert provider-shaped request templates, request hashes, and an offline gate summary showing exactly what the model would see. |
| **What does the firewall guarantee?** | Within the audited pipeline, fields with forbidden labels or inherited restricted provenance are excluded from the respondent packet; missing labels, unknown fields, label loss, scope loss, and missing required fields fail closed. |

Start with `examples/new_experiment_template/` and then follow `docs/ADAPTING_TO_A_NEW_EXPERIMENT.md`. The tutorial example is fully synthetic and requires no API key:

```bash
python3 scripts/audit_new_experiment.py
```


## Quick start

Requirements: Python 3.10+ and `numpy==2.3.5`.

```bash
python3 -m pip install -r requirements.lock
python3 scripts/reproduce_study1_offline.py
```

The full reproduction performs no API or network calls. It validates the frozen contracts, compiles all five contract batches in dry-run mode, verifies public-data hashes, reruns the frozen analysis, and compares the result with the released expected result.

For analysis only:

```bash
python3 scripts/reproduce_study1_analysis.py
```

## Repository map

- `causal_firewall/`: firewall, contract, dry-run, and frozen analysis code.
- `experiments/study1/`: access policy, 40 frozen experiment contracts, batch manifests, execution configuration, and frozen estimand registry.
- `data/CF-S1-CONFIRMATORY/`: deidentified semantic analysis data and expected results.
- `scripts/`: public verification and one-command reproduction entry points.
- `tests/`: focused offline tests for contracts, firewall compilation, and analysis integrity.
- `examples/new_experiment_template/`: blank inputs and a runnable synthetic adaptation example.
- `docs/`: design, analysis, data, and reproduction documentation.
- `results/`: manuscript-ready tables and audit crosswalks; useful but not required to execute the code.
- `UPLOAD_GUIDE.md`: folder-by-folder required/optional upload decisions.

## Public/private boundary

This package intentionally excludes API credentials, HMAC keys, the restricted unblinding crosswalk, raw provider response text, local authorization paths, signatures, and operational incident records. The public semantic dataset contains only the fields needed to reproduce the frozen analyses.
