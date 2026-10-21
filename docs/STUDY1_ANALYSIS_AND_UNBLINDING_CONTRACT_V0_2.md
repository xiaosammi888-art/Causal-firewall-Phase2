# Study 1 Analysis and Unblinding Contract — Joint Technical Freeze v0.2

**Project:** Causal Firewall  
**Contract ID:** `CF-S1-ANALYSIS-UNBLINDING-CONTRACT-V0.2-20261004`  
**Version:** `0.2.0`  
**Technical freeze date:** 2026-10-04  
**Status:** **FROZEN TECHNICAL SPECIFICATION — SIGNATURE-READY — NO CONFIRMATORY ANALYSIS OR UNBLINDING AUTHORITY**

## 1. Scope and authority

This contract freezes the Study 1 estimands, scoring rules, error structure, multiplicity rules, replication judgments, synthetic validation implementation, software environment, random seeds, and output schemas. It incorporates the prior blinded draft by hash while replacing every draft statistical default with the explicit rules below.

This technical freeze does not authorize access to a condition mapping, analysis of mapped P1-P5 outcomes, inspection of formal effects, API execution, rerunning, response replacement, expansion activation, or confirmatory unblinding. Those actions require a separate signed one-time authorization after the independent preflight and custodian-only mapping identity checks.

## 2. Incorporated blinded baseline

The following facts remain fixed:

1. Forty experiment contracts are frozen: 30 primary and 10 expansion.
2. B01-B05 are five contract-production batches; P1-P5 are five repeated sampling waves over the same 30 primary experiments.
3. All five blinded QC packages passed.
4. P1-P5 contain 38,400 logical response units in total.
5. The frozen blinded variance-only decision selected `N = 30` and activated no expansion experiment.
6. Every soft alert remains retained and descriptive; no alert can cause deletion, exclusion, replacement, reweighting, or rerunning.
7. Continuations and retries are transport history only and cannot change the logical sample definition.
8. No confirmatory unblinding, formal treatment effect, direction, p value, interval, or replication judgment has occurred.

The evidentiary paths and hashes in `docs/STUDY1_RESEARCH_STATE_RECOVERY_MEMO.md` and `docs/STUDY1_ANALYSIS_AND_UNBLINDING_CONTRACT_DRAFT.md` are incorporated without modification. The joint freeze manifest binds their exact hashes.

## 3. Frozen analytic population

- Include exactly the 30 primary experiments and P1-P5 logical responses bound by the frozen wave manifests.
- Exclude all 10 expansion-role contracts because the mechanical reassessment activated none.
- Pool P1-P5 into 100 logical draws per registered cell; wave is provenance, not an analysis factor or weight.
- Require exactly 38,400 unique logical responses and 39,600 component rows before mapping access.
- Fail closed on any missing, duplicate, nonfinite, out-of-schema, out-of-scale, hash-mismatched, or unauthorized record.
- Preserve all soft-alert observations and indicators.

## 4. Frozen estimands

The frozen registry contains 30 experiments, 33 components, and 28 source-paper clusters. For architecture `a`, cue `c`, experiment `j`, component `k`, and source arm `r`:

1. Decode component value `z` using the registry rule.
2. Compute `mu[a,c,j,k,r]` as the arithmetic mean over 100 logical responses.
3. Compute `delta_raw[a,c,j,k] = sum_r w[j,k,r] × mu[a,c,j,k,r]`.
4. Compute `delta[a,c,j,k] = benchmark_sign[j,k] × delta_raw[a,c,j,k]`.
5. Compute `gamma[a,j,k] = delta[a,aligned,j,k] − delta[a,reversed,j,k]`.
6. Compute `theta[j,k] = gamma[C,j,k] − gamma[D,j,k]`.
7. Compute `theta[j]` as the equal-weight arithmetic mean of registered `theta[j,k]` values.
8. Compute `theta_bar` as the equal-weight arithmetic mean of all 30 `theta[j]` values.

No inverse-variance, soft-alert, wave, article-size, or data-dependent weighting is permitted in the primary estimator.

## 5. Primary inference

- Hypothesis: `H0: E(theta[j]) ≤ 0` versus `H2: E(theta[j]) > 0`.
- Resample 28 source-paper identifiers with replacement for each replicate.
- Include all primary experiments belonging to every selected paper, preserving repeated selections.
- Use 20,000 replicates and seed `61001`.
- Standard error is the sample standard deviation of bootstrap means.
- Interval is the two-sided 2.5th and 97.5th percentile interval.
- Centered one-sided p value is `(1 + count(theta_bar_b − theta_bar >= theta_bar)) / 20,001`.
- Reject `H0` only when the p value is below `0.05`.
- This is the sole primary hypothesis and receives no multiplicity adjustment.

## 6. Frozen sensitivity analyses

Sensitivity analyses cannot replace or redefine the primary decision.

### 6.1 Article-equal mean

Average experiment estimates within each of the 28 source papers, then average paper means. Use 20,000 source-paper bootstrap replicates and seed `61002`.

### 6.2 CR2 intercept model

- Fit `theta[j] = beta_0 + error[j]` by ordinary least squares with 30 equal-weight experiments.
- Cluster by the 28 frozen source-paper identifiers.
- Use identity as the CR2 working covariance.
- For cluster `g`, use `A_g = (I_g − H_gg)^(-1/2)` and the CR2 sandwich variance.
- Compute Satterthwaite degrees of freedom from the coefficient-variance quadratic form: `df = trace(G)^2 / trace(G^2)`.
- Report `beta_0`, CR2 standard error, Satterthwaite degrees of freedom, two-sided t p value, and two-sided 95% t interval.
- Do not use the CR2 p value to alter the primary decision.

### 6.3 Within-experiment Monte Carlo variances

- Preserve the paired microblock/persona identity across architectures, cues, arms, and components.
- Recompute the complete experiment estimand separately for each of the 100 paired identifiers.
- Set `v_j = sample_variance(theta_microblock[j,1:100]) / 100`.
- A missing pair, duplicate pair, nonfinite variance, or variance not strictly greater than zero stops execution before effect output.

### 6.4 REML multilevel meta-analysis

- Fit `theta = beta_0 + u_paper + u_experiment + sampling_error`.
- Use `u_paper ~ N(0, tau_paper^2)`, `u_experiment ~ N(0, tau_experiment^2)`, and known diagonal sampling variances `v_j`.
- Use covariance `V = diag(v_j + tau_experiment^2) + tau_paper^2 Z Z'`.
- Estimate both variance components by restricted maximum likelihood with nonnegative constraints.
- Minimize `0.5 × [log|V| + log(1'V^-1 1) + (theta − beta_0 1)'V^-1(theta − beta_0 1) + 29 log(2π)]`.
- Use the deterministic optimizer frozen in the code: a 25 × 25 quartic-spaced grid, the best eight starts, bounded two-dimensional pattern search, a maximum of 160 refinement iterations, and at most four upper-bound expansions.
- Fail closed if the optimizer is nonfinite or terminates on its upper boundary.
- Use the unmodified Knapp-Hartung scale `q = Q / 29`, standard error `sqrt(q / (1'V^-1 1))`, 29 degrees of freedom, and a two-sided 95% t interval.
- Report both variance components, optimizer diagnostics, pooled estimate, standard error, interval, t statistic, and two-sided p value.
- Do not use REML output to alter the primary decision.

## 7. Replication diagnostics and multiplicity

- Replication effect for each registered component is `0.5 × delta[D,aligned] + 0.5 × delta[D,reversed]`.
- Resample the 100 paired microblock/persona identifiers with replacement 20,000 times while preserving both D cue labels and every D arm.
- Component seed is the unsigned integer represented by the first 16 hexadecimal characters of `SHA-256("CF-S1-REPLICATION|" + contract_id + "|" + component_id)`.
- Use the centered two-sided bootstrap p value.
- Apply Holm step-down adjustment jointly across all 33 registered components at familywise alpha `0.05`.
- Label a component `SUCCESS` only for a positive effect with adjusted p below `0.05`; label it `FAILURE` only for a negative effect with adjusted p below `0.05`; otherwise label it `INDETERMINATE`.
- A multi-component experiment is `SUCCESS` only if all components succeed, `FAILURE` if any component fails, and `INDETERMINATE` otherwise.

## 8. Frozen implementation and environment

The joint freeze manifest binds:

- the frozen contract and estimand registry;
- the analysis module, fixture generator, runner, and automated tests;
- Python `3.12.14` and NumPy `2.3.5` on the recorded macOS arm64 runtime;
- the exact dependency lock and runtime identity;
- all bootstrap and derived component seeds;
- the synthetic validation report and output schema; and
- individual and package-level SHA-256 values.

The implementation accepts only deterministic fixtures classified as `synthetic_test_fixture_no_mapping`. It rejects forbidden mapping/unblinding path tokens before reads, imports no network client, refuses to overwrite outputs, and records zero API and network calls.

## 9. Predeclared outputs

The frozen machine-readable output schema separates provenance, population audit, QC disclosures, primary estimates, experiment estimands, sensitivity analyses, replication diagnostics, deviations, and execution audit fields. No output may reveal raw mapping values.

Synthetic outputs must carry `synthetic_fixture_only_nonconfirmatory`, `confirmatory_analysis_authorized = false`, and `unblinding_authorized = false`.

## 10. Amendment control

Any change to a bound file invalidates this package hash. Before any mapping access, a change requires a blinded amendment, incremented version, new synthetic validation, new manifest, new receipt, and the same signatures. After mapping access, no amendment may redefine the confirmatory analysis.

## 11. Activation gates outside this technical freeze

The following are deliberately not supplied or authorized by this readable technical package:

1. custodian-only mapping path and SHA-256;
2. named individuals and completed signatures for all accountable roles;
3. independent preflight attestation;
4. exact one-time authorization window and output directory; and
5. a receipt explicitly setting `confirmatory_unblinding_authorized = true`.

Until all five gates are completed in separate controlled records, confirmatory analysis and unblinding remain prohibited. The technical freeze receipt must state `confirmatory_unblinding_authorized = false`.

## 12. Signature record

Signatures attest approval of this immutable technical specification; they do not themselves authorize unblinding.

| Approval | Printed name | Signature | Date/time | Status |
|---|---|---|---|---|
| Principal investigator |  |  |  | `PENDING` |
| Blinded analyst |  |  |  | `PENDING` |
| Unblinding custodian |  |  |  | `PENDING` |
| Independent auditor/witness |  |  |  | `PENDING` |

The exact contract hash, registry hash, code-package hash, environment hash, seed-register hash, validation-report hash, and technical freeze receipt hash are recorded in the joint freeze package generated from this contract.
