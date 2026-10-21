
.PHONY: test verify-data audit-example audit-contracts reproduce-analysis reproduce-offline

test:
	python3 -m unittest discover -s tests -v

verify-data:
	python3 scripts/verify_public_data.py

audit-example:
	python3 scripts/audit_new_experiment.py

audit-contracts:
	python3 scripts/run_study1_contract_audit.py

reproduce-analysis:
	python3 scripts/reproduce_study1_analysis.py

reproduce-offline:
	python3 scripts/reproduce_study1_offline.py
