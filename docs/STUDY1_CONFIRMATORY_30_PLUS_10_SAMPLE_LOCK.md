# Study 1 Confirmatory 30 + 10 Sample Lock

**Status:** The experiment-level sample allocation is frozen. This decision does not freeze future experiment contracts, modify the execution configuration, authorize API calls, or inspect confirmatory outcomes.

## Locked design

The eligible pool contains 40 dual-reviewed experiments from 33 source papers. The primary sample contains 30 experiments: 15 management and 15 psychology experiments from 28 source papers. Twenty primary experiments carry a sensitive social, ethical, gender, or race flag, exceeding the registered one-third coverage target. The remaining 10 experiments form a variance-triggered expansion pool.

The allocation used only outcome-blind engineering information: Reviewer 1 and Reviewer 2 passage, domain, source-paper cluster, archive engineering risk, feasibility, and adaptation boundary. It did not use human or LLM group means, treatment effects, p-values, signs, or replication success.

## Primary sample

| Candidate | Study | Domain | Source paper | Inventory risk | Sensitive |
|---|---|---|---|---|---|
| CF-S1-CAND-005 | AMJ_7_1 | management | AMJ_7 | low | yes |
| CF-S1-CAND-009 | JAP_2_3 | management | JAP_2 | moderate | yes |
| CF-S1-CAND-010 | JAP_3_1c | management | JAP_3 | moderate | no |
| CF-S1-CAND-011 | JAP_5_1 | management | JAP_5 | moderate | no |
| CF-S1-CAND-012 | JAP_6_4 | management | JAP_6 | moderate | yes |
| CF-S1-CAND-013 | JAP_7_3 | management | JAP_7 | moderate | yes |
| CF-S1-CAND-014 | JAP_8_3 | management | JAP_8 | low | yes |
| CF-S1-CAND-015 | JAP_9_6 | management | JAP_9 | moderate | yes |
| CF-S1-CAND-018 | OBHDP_2_1 | management | OBHDP_2 | low | yes |
| CF-S1-CAND-019 | OBHDP_3_5 | management | OBHDP_3 | low | yes |
| CF-S1-CAND-020 | OBHDP_4_1 | management | OBHDP_4 | low | yes |
| CF-S1-CAND-021 | OBHDP_5_2 | management | OBHDP_5 | low | no |
| CF-S1-CAND-022 | OBHDP_6_3 | management | OBHDP_6 | low | no |
| CF-S1-CAND-023 | OBHDP_7_2a | management | OBHDP_7 | low | yes |
| CF-S1-CAND-024 | OBHDP_8_2 | management | OBHDP_8 | low | yes |
| CF-S1-CAND-026 | JEP_1_6a | psychology | JEP_1 | moderate | yes |
| CF-S1-CAND-035 | JEP_10_3 | psychology | JEP_10 | moderate | yes |
| CF-S1-CAND-027 | JEP_2_2a | psychology | JEP_2 | low | yes |
| CF-S1-CAND-028 | JEP_2_2b | psychology | JEP_2 | low | yes |
| CF-S1-CAND-029 | JEP_3_1 | psychology | JEP_3 | low | yes |
| CF-S1-CAND-030 | JEP_5_3a | psychology | JEP_5 | low | yes |
| CF-S1-CAND-032 | JEP_6_4 | psychology | JEP_6 | high | no |
| CF-S1-CAND-034 | JEP_8_4 | psychology | JEP_8 | low | yes |
| CF-S1-CAND-036 | JPSP_1_2 | psychology | JPSP_1 | low | yes |
| CF-S1-CAND-047 | JPSP_10_1 | psychology | JPSP_10 | moderate | no |
| CF-S1-CAND-037 | JPSP_3_2 | psychology | JPSP_3 | low | yes |
| CF-S1-CAND-039 | JPSP_4_4 | psychology | JPSP_4 | low | no |
| CF-S1-CAND-040 | JPSP_4_7 | psychology | JPSP_4 | low | no |
| CF-S1-CAND-043 | JPSP_8_2 | psychology | JPSP_8 | moderate | no |
| CF-S1-CAND-045 | JPSP_9_1 | psychology | JPSP_9 | low | no |

## Ordered expansion pool

The blinded reassessment may select only totals 30, 32, 34, 36, 38, or 40. The required count is rounded upward to the next allowed total, and complete waves are activated in the order below.

| Wave | Management | Psychology | Cumulative total |
|---:|---|---|---:|
| 1 | AMJ_6_2 | JPSP_9_3 | 32 |
| 2 | AMJ_5_1 | JEP_5_3b | 34 |
| 3 | AMJ_9_1 | JPSP_3_3 | 36 |
| 4 | OBHDP_1_2a | JPSP_10_3 | 38 |
| 5 | — | JEP_1_1b, JPSP_7_6 | 40 |

`JPSP_7_6` is intentionally last. It remains eligible for the firewall contrast but must be interpreted as a synthetic-persona calibration contrast rather than a randomized human country effect.

## Blinded variance reassessment

The locked interim subset contains five management and five psychology experiments selected by SHA-256 rank under the fixed seed phrase `CF-S1-30PLUS10-20260929`. The reassessment may use only the standard deviation or variance of paired contrasts. It must conceal the mean, sign, condition labels, treatment-effect direction, p-values, and replication success.

If 30 experiments retain the registered power, no expansion experiment is activated. Otherwise, the required count is rounded upward and the corresponding complete waves are activated. API draws are not the inferential sample and cannot replace experiment-level expansion.

## Replacement and execution boundaries

Before any confirmatory outcome is generated, a hard-gate failure in a primary experiment promotes the earliest same-domain expansion candidate. Replenishing the expansion pool requires a separately dual-reviewed reserve. Once outcomes exist, no replacement may depend on effect size, sign, p-value, or replication success.

This lock does not draft or freeze Batch 04 or Batch 05 contracts and does not authorize any model or API execution.
