# New Experiment Starter

This folder is a scholar-facing starter kit for adapting the causal firewall to a new social-science experiment.

## Contents

- `experiment_contract.template.json`: a valid draft scaffold with explicit replacement markers.
- `access_policy.template.json`: a deny-by-default provenance policy suitable for most between-subjects studies.
- `completed_example/experiment_contract.json`: a fully specified synthetic two-arm example that can be audited immediately.

The completed example is fictional and is not adapted from a copyrighted instrument or an existing empirical study.

## Run the completed example

From the repository root:

```bash
python3 scripts/audit_new_experiment.py
```

The command validates the contract, creates eight inert request templates (two arms × two cue directions × two architectures), and writes a summary under `reproduction_outputs/new_experiment_example/`. It never reads credentials or calls a model.

Expected result:

- Architecture C admits the contaminated `summary_context` because its field name is whitelisted.
- Architecture D denies the same field because its provenance inherits the `RESEARCH_RESTRICTED` label.
- Both architectures retain every required participant-visible field.
- Every prepared request is stateless and network-disabled.

## Adapt the blank scaffold

1. Copy `experiment_contract.template.json` to a new project directory.
2. Replace every string beginning with `REPLACE_`.
3. Keep the contract in `draft` status while editing and leave `normalized_material_sha256` as `null`.
4. Validate and audit it:

```bash
python3 scripts/audit_new_experiment.py \
  --contract path/to/experiment_contract.json \
  --policy examples/new_experiment_template/access_policy.template.json
```

5. Review all generated request templates before any live execution.
6. Freeze the materials and record their normalized hash only after author review.

See `docs/ADAPTING_TO_A_NEW_EXPERIMENT.md` for the complete workflow and extension points.
