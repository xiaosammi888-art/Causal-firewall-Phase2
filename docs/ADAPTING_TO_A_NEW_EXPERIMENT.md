# Adapting the Causal Firewall to a New Experiment

This guide explains how another scholar can use the infrastructure for a new between-subjects social-science experiment. The adaptation workflow is deliberately offline first: no model call should occur until the contract, policy, and generated request packets have been reviewed.

## 1. What you provide

You provide two declarative inputs:

1. **Experiment contract.** The contract records provenance, population scope, experimental arms, participant-visible materials, outcome items, researcher-restricted expectations, and execution status.
2. **Access policy.** The policy defines which information labels the simulated respondent may receive and applies deny-by-default inheritance rules to derived fields.

Start with:

- `examples/new_experiment_template/experiment_contract.template.json`
- `examples/new_experiment_template/access_policy.template.json`

## 2. Separate participant-visible and research-restricted information

Place only information that a real participant should receive under `materials`, `population`, and participant-facing outcome items. Put hypotheses, expected directions, human benchmarks, opposite-arm materials, analysis decisions, and audit feedback behind restricted labels.

The participant packet should normally contain only:

- participant role;
- the current synthetic persona;
- common scenario;
- current-arm stimulus;
- participant-facing outcome items;
- strict response schema.

Do not solve leakage by deleting provenance. A derived summary remains restricted when any upstream source is restricted.

## 3. Keep the contract in draft status

While editing:

```json
"normalized_material_sha256": null
```

and:

```json
"contract_status": "draft",
"paid_calls_authorized": false
```

The validator rejects draft contracts that authorize paid calls. Freeze only after materials, outcome coding, persona fields, and arm definitions have been independently reviewed.

## 4. Run the offline audit

Try the completed fictional example first:

```bash
python3 scripts/audit_new_experiment.py
```

Then audit your own files:

```bash
python3 scripts/audit_new_experiment.py \
  --contract path/to/experiment_contract.json \
  --policy path/to/access_policy.json
```

The command validates the contract and compiles every arm and cue direction under both comparison architectures:

- **C — fresh-context manual whitelist:** decides from field names and therefore admits the contaminated `summary_context`.
- **D — labeled causal firewall:** evaluates labels, provenance, lineage, stage, and arm scope and therefore denies the same contaminated field.

The command creates provider-shaped JSON requests but contains no HTTP client, never reads credentials, and reports zero network calls.

## 5. Inspect the outputs

Outputs appear under `reproduction_outputs/new_experiment_example/<run-id>/`:

- `summary.json`: gate status, allowed and denied fields, cue-boundary checks, and request hashes;
- `requests/*.json`: inert request envelopes showing exactly what the model would see.

Before any live execution, confirm that:

1. every required participant-visible field is present;
2. the current-arm stimulus is present and every other-arm stimulus is absent;
3. hypotheses, expected directions, benchmarks, and audit feedback are absent under Architecture D;
4. response schemas include every registered item and no model-written aggregate;
5. requests are stateless, use no tools, set storage to false, and contain no previous-response identifier;
6. no API call is authorized by the contract.

## 6. Freeze the experiment

After review:

1. calculate the normalized material hash with `causal_firewall.study1_contract.normalized_material_hash`;
2. write the hash to `source.normalized_material_sha256`;
3. change `execution.contract_status` from `draft` to `frozen`;
4. retain `paid_calls_authorized: false` until a separate execution decision;
5. record the contract file hash, policy hash, model snapshot, decoding settings, and analysis plan in a freeze manifest.

Freezing establishes what was fixed before outcome inspection. It does not itself authorize paid execution.

## 7. Add a provider or model family

The current public adapter serializes an OpenAI-shaped dry request, but the firewall is upstream of the provider. A new adapter should accept only a successful `PacketBuildResult`, serialize no additional research state, disable storage and tools by default, expose the exact model-visible payload for hashing, and pass equivalent stateless-request tests.

Provider-specific network behavior, retries, caching, tools, and conversation state require a separate noninterference audit. Do not assume that passing one provider's adapter validates another provider.

## 8. What the firewall guarantees

For fields that pass through the tagged-field and policy pipeline, the infrastructure provides an executable, auditable guarantee that disallowed labels or inherited restricted provenance do not enter the generated respondent packet. It also fails closed on missing labels, unknown fields, label loss, scope loss, and missing required participant fields.
