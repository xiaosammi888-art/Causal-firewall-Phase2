# Study 1 Confirmatory Analysis Synthetic Harness

## Purpose

This harness tests the estimand construction, source-paper cluster bootstrap, article-equal sensitivity, CR2 cluster-robust sensitivity, REML multilevel sensitivity, component-level replication bootstrap, Holm adjustment, and replication-label rules specified in the blinded v0.2 Analysis and Unblinding Contract and its estimand registry.

It is a synthetic, nonconfirmatory implementation check. It has no authority to analyze real confirmatory data or perform unblinding.

## Safety boundary

- The loader accepts only fixtures classified as `synthetic_test_fixture_no_mapping`.
- Every fixture value must exactly match the deterministic synthetic generator; changing values and recomputing hashes still fails closed.
- Paths containing `restricted`, `crosswalk`, `unblinding`, or `unblind` are rejected before reading.
- No condition-mapping input is accepted.
- No network or API client is used.
- Existing output directories are never overwritten.
- Results and replication labels are synthetic test outputs only.

## Run

From the repository root, choose new output directories and run:

```bash
python3 scripts/generate_study1_confirmatory_synthetic_fixture.py \
  .artifact_tool/study1_synthetic_fixture

python3 scripts/run_study1_confirmatory_synthetic_analysis.py \
  .artifact_tool/study1_synthetic_fixture \
  .artifact_tool/study1_synthetic_analysis
```

The generator uses eight deterministic draws per architecture-cue-arm-component cell by default. The analysis runner uses the contract seeds and 20,000 bootstrap replicates by default.

## Validate

```bash
python3 -m unittest -v tests.test_study1_confirmatory_analysis_blinded
```

The test suite checks deterministic results, the 30-experiment/33-component/28-source-paper registry scope, mapping-free declarations, forbidden paths, Cartesian completeness, value integrity, Holm adjustment, Student-t reference values, the singleton-cluster CR2 identity, and deterministic REML failure handling.

## Frozen sensitivity details

- CR2 uses an intercept-only OLS model, source-paper clusters, identity working covariance, the CR2 adjustment, and Satterthwaite quadratic-form degrees of freedom.
- Within-experiment Monte Carlo variance is the sample variance of paired microblock-level experiment estimands divided by the draw count; zero or nonfinite variance fails closed.
- REML uses a source-paper random intercept, a separate experiment-level heterogeneity component, constrained nonnegative variance components, and a deterministic grid-plus-pattern-search optimizer.
- The REML interval uses the unmodified Knapp-Hartung scale and `k - 1` degrees of freedom.

This harness does not read P1-P5 datasets, does not use a condition crosswalk, and does not produce formal Study 1 findings.
