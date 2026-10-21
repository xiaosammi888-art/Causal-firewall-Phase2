# Study 1 Confirmatory Execution Configuration V2: 30 Primary + 10 Expansion

**Status:** Frozen execution plan and offline schedules; no API authorization.

## Locked model and decoding

- Snapshot: `gpt-5.4-mini-2026-03-17`
- Responses API; Standard service tier
- `reasoning.effort=none`, `temperature=1.0`, `top_p` and provider seed unset
- Strict JSON Schema; tools disabled; storage disabled

GPT-5.4 Mini is retained for comparability with the engineering pilot. The current model page still lists this exact snapshot and required features. The official latest-model page now points to GPT-6 Astra, but changing model generation at confirmation would add a model-change confound.

## Primary execution

- 30 experiments, 96 arms, 384 architecture-by-cue cells
- Compatibility PC0: 384 calls, excluded from analysis, USD 1.00 cap
- P1-P5: 20 draws per cell and 7,680 calls per wave
- 100 confirmatory draws per cell: 38,400 calls
- Primary maximum including compatibility: 38,784 calls
- Planning estimate: USD 55.98; primary hard cap: USD 71.00

## Blinded expansion

After P5, the locked variance-only reassessment selects N=30/32/34/36/38/40. Means, signs, labels, p-values, directions, and replication outcomes remain hidden. Each activated branch receives one compatibility draw and 100 confirmatory draws per activated cell.

| Final N | Expansion cells | Added calls | Added estimate | Compatibility cap | Per 20-draw wave cap | Branch cap |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 32 | 3,232 | USD 5.94 | USD 0.10 | USD 1.60 | USD 8.10 |
| 34 | 64 | 6,464 | USD 11.98 | USD 0.20 | USD 3.20 | USD 16.20 |
| 36 | 88 | 8,888 | USD 15.58 | USD 0.25 | USD 4.10 | USD 20.75 |
| 38 | 120 | 12,120 | USD 21.43 | USD 0.35 | USD 5.60 | USD 28.35 |
| 40 | 144 | 14,544 | USD 24.19 | USD 0.40 | USD 6.50 | USD 32.90 |

## Maximum envelope

- Maximum calls: 53,328
- Maximum planning estimate: USD 80.17
- Global cumulative hard cap: USD 104.00
- Cached-input discounts are not assumed
- Every compatibility or 20-draw wave requires a separate single-use, hash-bound authorization

## Offline verification

- Gates: 17/17 passed
- Network calls: 0
- Model calls: 0
- Authorization files: none

## Official references

- Model: https://developers.openai.com/api/docs/models/gpt-5.4-mini
- Pricing: https://developers.openai.com/api/docs/pricing
- Latest-model guidance: https://developers.openai.com/api/docs/guides/latest-model
