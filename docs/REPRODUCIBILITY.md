# Study 1 Reproducibility

## Environment

- Python 3.10 or later
- `numpy==2.3.5`
- No API key is required
- The reproduction scripts make no network calls

Install the locked dependency:

```bash
python3 -m pip install -r requirements.lock
```

## Full offline reproduction

```bash
python3 scripts/reproduce_study1_offline.py
```

This command:

1. verifies the public-data SHA-256 manifest;
2. runs the focused unit tests;
3. validates all 40 frozen contracts;
4. runs the reusable new-experiment tutorial and checks the C-versus-D cue boundary;
5. compiles all five frozen batches into inert provider-shaped request templates;
6. recomputes the confirmatory and sensitivity analyses from the public semantic data;
7. compares all analytic result sections with the released frozen result.

Generated files are written under `reproduction_outputs/`, which is ignored by Git.

## Analysis only

```bash
python3 scripts/reproduce_study1_analysis.py
```

The expected output ends with `exact_analysis_match=true`. The script compares the primary result, all 30 experiment estimands, article-equal sensitivity, CR2, REML, within-experiment variances, and all replication diagnostics.

## Contract and firewall audit only

```bash
python3 scripts/validate_study1_contracts.py
python3 scripts/run_study1_contract_audit.py
```

The dry-run audit emits request templates but never reads credentials, authorizes paid calls, or contacts a provider.
