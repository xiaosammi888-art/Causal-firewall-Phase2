# Study 1 Manuscript Ready Methods and Results

## Confirmatory analysis methods

Confirmatory analyses followed the prespecified Study 1 Analysis and Unblinding Contract. The analytic population comprised the 30 primary experiments sampled across five repeated waves (P1-P5); none of the 10 expansion experiments was activated. The pooled data contained 38,400 logical response units and 39,600 component rows. All observations associated with blinded soft alerts were retained, and technical continuations or retries did not alter the logical sample. For experiment j, the confirmatory estimand was theta_j = gamma_C,j - gamma_D,j, where gamma was the aligned-minus-reversed contrast and C and D denoted the fresh-context manual-whitelist and labeled causal-firewall architectures, respectively. The primary estimate was the equal-weight mean of theta_j across the 30 experiments. Inference used 20,000 bootstrap samples of the 28 source-paper identifiers (seed 61001), with a one-sided test of H0: E(theta_j) <= 0. The sole primary test was evaluated at alpha = .05 without multiplicity adjustment.

## Sensitivity analysis methods

We assessed robustness using three prespecified sensitivity analyses. First, we averaged experiment estimates within source papers and then averaged across the 28 papers, with 20,000 source-paper bootstrap samples (seed 61002). Second, we estimated an equal-weight intercept-only model with CR2 standard errors clustered by source paper and Satterthwaite degrees of freedom. Third, we fit the prespecified REML multilevel meta-analysis with source-paper and experiment-level heterogeneity components, known within-experiment Monte Carlo variances, and unmodified Knapp-Hartung inference. These analyses were sensitivity checks and did not replace the primary decision.

## Replication diagnostics methods

Replication diagnostics were evaluated separately from the confirmatory theta_j estimand. For each of the 33 registered components, the replication effect averaged the D-architecture aligned and reversed effects. We used 20,000 paired-microblock bootstrap samples per component and applied Holm step-down correction jointly across all 33 components at familywise alpha = .05. A component was classified as SUCCESS for a positive effect with Holm-adjusted p < .05, FAILURE for a negative effect with Holm-adjusted p < .05, and INDETERMINATE otherwise. A multi-component experiment was classified as SUCCESS only when all components succeeded, FAILURE when any component failed, and INDETERMINATE otherwise.

## Confirmatory results

The primary confirmatory estimate was positive, theta_bar = 0.100 (SE = 0.027, 95% CI [0.048, 0.153], one-sided p = 0.00025). According to the prespecified decision rule, we rejected H0. Operationally, the aligned-versus-reversed contrast was larger under the fresh-context manual-whitelist architecture than under the labeled causal-firewall architecture.

## Sensitivity results

The sensitivity analyses yielded the same directional conclusion. The article-equal estimate was 0.094 (SE = 0.026, 95% CI [0.044, 0.147], one-sided p = 0.00020). The CR2 estimate was 0.100 (SE = 0.027, t(25.48) = 3.68, 95% CI [0.044, 0.156], two-sided p = 0.00109). The REML estimate was 0.096 (SE = 0.027, t(29) = 3.60, 95% CI [0.041, 0.150], two-sided p = 0.00116). The REML paper-level and experiment-level variance components were 0.0160 and 0.0032, respectively.

## Replication results

After Holm correction, 24 of the 33 registered components were classified as SUCCESS, 4 as FAILURE, and 5 as INDETERMINATE. At the experiment level, 21 of 30 experiments were classified as SUCCESS, 4 as FAILURE, and 5 as INDETERMINATE. These replication classifications concern the D-architecture replication effect and should not be inferred from the sign of the separate theta_j estimand.

## Table 1 Confirmatory and sensitivity analyses

| Analysis | Estimate | SE | 95% CI | p | Sidedness | Role |
|---|---:|---:|---:|---:|---|---|
| Primary source-paper bootstrap | 0.0999 | 0.0267 | [0.0480, 0.1531] | 0.0002499875 | One-sided | REJECT_H0 |
| Article-equal bootstrap | 0.0942 | 0.0263 | [0.0437, 0.1468] | 0.00019999 | One-sided | Sensitivity |
| CR2 intercept model | 0.0999 | 0.0271 | [0.0441, 0.1557] | 0.0010895659 | Two-sided | Sensitivity |
| REML multilevel meta-analysis | 0.0959 | 0.0266 | [0.0415, 0.1504] | 0.0011638878 | Two-sided | Sensitivity |

**Note.** The primary and article-equal p values are one-sided centered-bootstrap values. CR2 and REML p values are two-sided. Sensitivity analyses do not alter the frozen primary decision.

## Table 2 Replication classification summary

| Level | SUCCESS | FAILURE | INDETERMINATE | Total |
|---|---:|---:|---:|---:|
| Registered components | 24 | 4 | 5 | 33 |
| Registered experiments | 21 | 4 | 5 | 30 |

**Note.** Holm correction was applied jointly across all 33 registered components. Experiment-level judgments follow the frozen all-components rule.

## Table 3 Experiment level confirmatory and replication results

| Contract | Source study | Source paper | theta_j | Replication |
|---|---|---|---:|---|
| CF-S1-CONF-001 | AMJ_7_1 | AMJ_7 | 0.254375 | FAILURE |
| CF-S1-CONF-002 | JAP_8_3 | JAP_8 | 0.001000 | INDETERMINATE |
| CF-S1-CONF-003 | OBHDP_3_5 | OBHDP_3 | 0.417700 | SUCCESS |
| CF-S1-CONF-004 | OBHDP_4_1 | OBHDP_4 | 0.103333 | INDETERMINATE |
| CF-S1-CONF-005 | JEP_2_2a | JEP_2 | 0.035417 | SUCCESS |
| CF-S1-CONF-006 | JEP_5_3a | JEP_5 | 0.084667 | SUCCESS |
| CF-S1-CONF-007 | JEP_8_4 | JEP_8 | -0.006667 | FAILURE |
| CF-S1-CONF-008 | JPSP_3_2 | JPSP_3 | 0.131800 | SUCCESS |
| CF-S1-CONF-009 | OBHDP_2_1 | OBHDP_2 | 0.173889 | SUCCESS |
| CF-S1-CONF-010 | OBHDP_5_2 | OBHDP_5 | 0.104444 | SUCCESS |
| CF-S1-CONF-011 | OBHDP_6_3 | OBHDP_6 | 0.400208 | SUCCESS |
| CF-S1-CONF-012 | OBHDP_7_2a | OBHDP_7 | 0.261667 | FAILURE |
| CF-S1-CONF-013 | JEP_3_1 | JEP_3 | 0.028333 | SUCCESS |
| CF-S1-CONF-014 | JPSP_1_2 | JPSP_1 | 0.059333 | SUCCESS |
| CF-S1-CONF-015 | JPSP_4_4 | JPSP_4 | 0.242500 | SUCCESS |
| CF-S1-CONF-016 | JPSP_9_1 | JPSP_9 | 0.005650 | INDETERMINATE |
| CF-S1-CONF-017 | JAP_3_1c | JAP_3 | -0.079167 | SUCCESS |
| CF-S1-CONF-018 | JAP_7_3 | JAP_7 | 0.020000 | INDETERMINATE |
| CF-S1-CONF-019 | JAP_9_6 | JAP_9 | -0.192000 | SUCCESS |
| CF-S1-CONF-020 | OBHDP_8_2 | OBHDP_8 | -0.143542 | SUCCESS |
| CF-S1-CONF-021 | JEP_2_2b | JEP_2 | 0.132500 | SUCCESS |
| CF-S1-CONF-023 | JPSP_4_7 | JPSP_4 | 0.308750 | INDETERMINATE |
| CF-S1-CONF-026 | JAP_2_3 | JAP_2 | 0.167500 | SUCCESS |
| CF-S1-CONF-027 | JAP_5_1 | JAP_5 | 0.163333 | SUCCESS |
| CF-S1-CONF-028 | JAP_6_4 | JAP_6 | -0.015200 | SUCCESS |
| CF-S1-CONF-029 | JEP_1_6a | JEP_1 | 0.039167 | SUCCESS |
| CF-S1-CONF-030 | JEP_10_3 | JEP_10 | 0.019100 | FAILURE |
| CF-S1-CONF-031 | JPSP_8_2 | JPSP_8 | 0.023958 | SUCCESS |
| CF-S1-CONF-032 | JPSP_10_1 | JPSP_10 | 0.081500 | SUCCESS |
| CF-S1-CONF-037 | JEP_6_4 | JEP_6 | 0.173333 | SUCCESS |

## Table 4 Component level replication results

| Component | Source paper | Effect | SE | 95% CI | Raw p | Holm p | Label |
|---|---|---:|---:|---:|---:|---:|---|
| CF-S1-CONF-001:primary | AMJ_7 | -0.090938 | 0.014864 | [-0.119688, -0.061250] | 4.99975e-05 | 0.0016499175 | FAILURE |
| CF-S1-CONF-002:primary | JAP_8 | 0.000000 | 0.000000 | [0.000000, 0.000000] | 1 | 1 | INDETERMINATE |
| CF-S1-CONF-003:primary | OBHDP_3 | 0.042950 | 0.006480 | [0.030350, 0.055850] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-004:primary | OBHDP_4 | -0.012500 | 0.005180 | [-0.022500, -0.002500] | 0.014899255 | 0.05959702 | INDETERMINATE |
| CF-S1-CONF-005:primary | JEP_2 | 0.209167 | 0.007412 | [0.194583, 0.223542] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-006:primary | JEP_5 | 0.520333 | 0.008024 | [0.504829, 0.536000] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-007:primary | JEP_8 | -0.226667 | 0.013706 | [-0.253333, -0.200000] | 4.99975e-05 | 0.0016499175 | FAILURE |
| CF-S1-CONF-008:primary | JPSP_3 | 0.034650 | 0.008105 | [0.018350, 0.050100] | 9.9995e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-009:primary | OBHDP_2 | 0.078611 | 0.009989 | [0.059167, 0.098333] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-010:primary | OBHDP_5 | 0.209444 | 0.006560 | [0.196667, 0.222222] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-011:primary | OBHDP_6 | 0.026979 | 0.005306 | [0.016771, 0.037396] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-012:primary | OBHDP_7 | -0.041250 | 0.013836 | [-0.067917, -0.013750] | 0.0025498725 | 0.015299235 | FAILURE |
| CF-S1-CONF-013:coprimary_harm | JEP_3 | 0.029167 | 0.008906 | [0.011667, 0.046667] | 0.00159992 | 0.01119944 | SUCCESS |
| CF-S1-CONF-013:coprimary_instrumental | JEP_3 | 0.875833 | 0.010082 | [0.855833, 0.895000] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-014:primary | JPSP_1 | 0.068500 | 0.008094 | [0.052665, 0.084169] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-015:primary | JPSP_4 | 0.160417 | 0.008578 | [0.143750, 0.177083] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-016:bolstering_minus_point | JPSP_9 | 0.147850 | 0.003825 | [0.140350, 0.155350] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-016:backdown_minus_point | JPSP_9 | 0.006250 | 0.003846 | [-0.001250, 0.013800] | 0.10579471 | 0.31738413 | INDETERMINATE |
| CF-S1-CONF-017:primary | JAP_3 | 0.127083 | 0.007981 | [0.111250, 0.142639] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-018:primary | JAP_7 | 0.012500 | 0.018236 | [-0.022500, 0.048889] | 0.49037548 | 0.98075096 | INDETERMINATE |
| CF-S1-CONF-019:primary | JAP_9 | 0.239250 | 0.014082 | [0.212000, 0.267250] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-020:upb_minus_usb | OBHDP_8 | 0.267396 | 0.023260 | [0.222292, 0.313750] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-020:upb_minus_control | OBHDP_8 | 0.261354 | 0.022915 | [0.217604, 0.306771] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-021:primary | JEP_2 | 0.322708 | 0.005614 | [0.311667, 0.333750] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-023:primary | JPSP_4 | -0.016563 | 0.006440 | [-0.029375, -0.004063] | 0.01039948 | 0.0519974 | INDETERMINATE |
| CF-S1-CONF-026:primary | JAP_2 | 0.765000 | 0.005154 | [0.754583, 0.774792] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-027:primary | JAP_5 | 0.020250 | 0.004549 | [0.011333, 0.029083] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-028:primary | JAP_6 | 0.009200 | 0.001075 | [0.007133, 0.011267] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-029:primary | JEP_1 | 0.195833 | 0.011498 | [0.172917, 0.217917] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-030:primary | JEP_10 | -0.029350 | 0.004214 | [-0.037700, -0.021050] | 4.99975e-05 | 0.0016499175 | FAILURE |
| CF-S1-CONF-031:primary | JPSP_8 | 0.189271 | 0.009779 | [0.170206, 0.208333] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-032:primary | JPSP_10 | 0.846000 | 0.007579 | [0.830750, 0.860750] | 4.99975e-05 | 0.0016499175 | SUCCESS |
| CF-S1-CONF-037:primary | JEP_6 | 0.397500 | 0.022572 | [0.353333, 0.441667] | 4.99975e-05 | 0.0016499175 | SUCCESS |

## Use restrictions

This package reports the frozen confirmatory analysis only. Any additional model, subgroup analysis, transformation, exclusion, or visualization not already contained in the frozen result must be labeled post-unblinding exploratory. The internal legacy status strings attached to the CR2 and REML objects are preserved in the audit source but are not manuscript claims; formal provenance is governed by the authorized top-level execution and final freeze records.
