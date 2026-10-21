# Phase2 Confirmatory Design

## Confirmatory objective

Phase 2 tests whether provenance-aware information control attenuates the effect of hidden research expectations on LLM-simulated treatment effects across experiments. 

## Sampling frame

Select 30 experiments not used in Phase 1. The frozen sample should contain 15 management and 15 psychology experiments, approximately half with high prompt or causal ambiguity, at least one third involving sensitive social attributes or norms, and no more than two experiments from one source article. Sampling and exclusions must be registered before human or LLM results are inspected.

Cross every experiment with three model families: one OpenAI model, one commercial model from another provider, and one versioned open-weight model. Treat model as a crossed fixed factor in the primary analysis. Three levels are too few to support a stable population-level random-effect claim about models.

## Experimental factors

The primary factorial design contains architecture C versus D, aligned versus reversed hypothesis cue, and every original treatment arm. The same source materials, outcome coding, and contaminated derived summary must feed C and D. C admits that summary through a field-name whitelist. D rejects it through inherited labels and centralized policy.

A and B are secondary architecture conditions. A receives the hypothesis directly in a monolithic context. B receives it through default handoff history. Use one shared no-cue condition when the resulting inference payloads are byte-equivalent; do not create nominal architecture observations from identical requests merely to inflate the design.

## Estimands

For architecture a, hypothesis cue c, experiment j, and model m, first estimate the original experiment treatment effect Delta. For binary outcomes, Delta is a risk difference. For continuous outcomes, use the preregistered standardized or raw mean difference appropriate to the source experiment.

Define directional cue sensitivity as

`Gamma_ajm = Delta_a aligned jm minus Delta_a reversed jm`.

Define the primary firewall contrast as

`Theta_jm = Gamma_Cjm minus Gamma_Djm`.

Positive Theta means that the hypothesis direction changed the estimated treatment effect more under the manual whitelist than under the labeled firewall.

## Hypotheses and decision rules

H1 is structural noninterference. Every D request must have zero prohibited fields, zero canary hits, and one inference-payload hash across cue labels for a given legal participant packet. Any violation stops the affected run and opens a versioned policy correction. It is not averaged away.

H2 is the single primary behavioral hypothesis: the mean Theta across source experiments and models is greater than zero. Test H2 one-sided at alpha 0.05.

H3a and H3b compare Gamma A and Gamma B with Gamma D. Apply Holm correction across these two secondary tests.

H4 is the no-cue negative control. Byte-equivalent requests define one shared response distribution. Label-specific differences are reported as Monte Carlo variation and are not interpreted as architecture effects.

Cross-arm contamination and post-outcome hypothesis inference are secondary modules. They require separate contracts and must not write information back to the respondent before outcome lock.

## Sample size

Use 30 source experiments as the planned scientific sample. Under a conservative paired normal approximation, 30 experiments provide about 80 percent power for a one-sided alpha 0.05 test when the standardized mean firewall contrast is approximately 0.45. This calculation deliberately counts experiments rather than API calls.

Phase 1 observed a raw C-minus-D Gamma contrast of 0.333 in one experiment. Phase 2 defines 0.15 risk-difference units as the minimum meaningful contrast for binary-outcome tasks. Because one pilot cannot estimate between-experiment variance, conduct a blinded variance reassessment after ten experiments. Use only the standard deviation of paired contrasts, conceal the mean and sign, and increase the total sample from 30 to at most 40 if needed to retain 80 percent power for the registered minimum effect.

Within each experiment-model pair, collect 100 draws for every primary architecture-cue-arm cell. With two architectures, two cue directions, and two
arms, this is 800 calls per experiment-model and 72,000 primary calls for 30 experiments and three models. Collect 50 draws for secondary A and B cells and 50 per arm for the shared no-cue baseline, adding 45,000 calls. The total plan is 117,000 calls before any separately authorized cross-arm module.

At 100 draws per binary cell, the worst-case Monte Carlo standard error of one Gamma is 0.10. This precision is sufficient for experiment-level aggregation; increasing calls beyond this point should be justified by measurement error, not by a desire to manufacture smaller p values.

## Analysis

Compute cell outcomes and treatment effects before fitting the cross-experiment model. The primary analysis uses paired Theta values with experiment random intercepts, fixed model effects, and source-article clustering. Report the mean contrast, a 95 percent confidence interval, and the proportion of experiments with positive Theta. Use an article-level cluster bootstrap as the primary interval estimator and a multilevel meta-analytic model as a sensitivity analysis.

Do not treat API draws as the inferential sample. A response-level logistic or linear model may diagnose cell behavior, but confirmatory uncertainty must reflect variation across experiments and source articles.

## Execution and missingness

Freeze model snapshots, prompts, schemas, temperature, storage, tool access, contracts, policies, and hashes before the first paid call. Randomize call order within model and execution batch. Record batch and timestamp so temporal drift can be diagnosed.

Content retries are prohibited. A transport retry is allowed only when the provider returned no completed response; it must reuse the exact request hash and receive a nonzero transport-retry identifier. Invalid structured outputs remain failures and are included in the protocol-failure rate.

Model or experiment exclusions require a reason that was registered before outcomes were inspected. If a snapshot becomes unavailable, treat the replacement as a new model version and report it separately.
