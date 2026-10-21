# Study 1 Manuscript Results Audit Checklist

## Frozen source

- [x] Final freeze manifest SHA-256: `aca4d95ad906b058891ad8e582e4825aef6204a1ae265638396d3bcc7917bb9c`
- [x] Final freeze receipt SHA-256: `f8f43cc9e4557e05ad84f93da41277298d55db51c450e74fb524ae220a13bc20`
- [x] Controlled extraction SHA-256: `4d4a62bf10bc4ec7918b5428574fdea307fe740464b6f38a04c2687813eaebcf`
- [x] Formal result SHA-256: `ea9de8899c60ab256a0eef429968ffb32866ebfcd23639bff166a488cf203162`
- [x] Primary decision copied without reinterpretation: `REJECT_H0`
- [x] No additional model, exclusion, weighting rule, or rerun introduced.

## Content checks

- [x] Population counts match the frozen extraction.
- [x] Primary estimate, standard error, interval, p value, and decision match.
- [x] Article-equal, CR2, and REML values match.
- [x] Replication counts match at component and experiment levels.
- [x] Table 3 contains all 30 experiment records.
- [x] Table 4 contains all 33 component records.
- [x] Raw and Holm-adjusted p values are labeled distinctly.
- [x] Replication labels are not inferred from the sign of theta_j.
- [x] The CR2 and REML legacy status strings are treated as audit metadata, not manuscript claims.

## Before submission

- [ ] Confirm journal notation and table style without changing numerical values.
- [ ] Verify every edited manuscript number against `MANUSCRIPT_AUDIT_CROSSWALK.csv`.
- [ ] Label any subsequently added analysis as post-unblinding exploratory.
- [ ] Exclude mapping, restricted envelope, and restricted consumption-package materials from shared files.
