# Exploratory & Investigation Scripts

This directory contains standalone exploratory, diagnostic, and probe scripts developed during Brief 3 investigations (analytics linking analysis, log-trace correlation verification, rule coverage audits, and historical identifier cross-checks).

These scripts are not part of the operational production pipeline (`code/main.py`). The maintained operational tools remain at the parent level (`code/tools/`):
- `preflight.py`: Pre-submission integrity, temporal cutoff assertions, and format checker.
- `package_submission.py`: Packages submission `code.zip` and verifies structure and dual evaluation directories.
- `check_log.py`: Validates `log.txt` turn-by-turn against AGENTS.md rules.
- `stats_from_output.py`: Computes official distributions and step totals directly from `output.csv`.
- `consistency_check.py`: Reconciles metrics between documents and output artifacts.
- `doc_claims_check.py`: Validates factual claims across Markdown documentation.
- `append_turn_log.py`: Structured logger for agent conversation turns.
