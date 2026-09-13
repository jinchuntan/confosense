> **Historical document ? status changed 13 September 2026.** This retained account predates the integration repairs. Its performance/achievement statements do not establish current findings. See `INTEGRATION_REPAIR_REPORT.md` at the repository root and `audit/integration_repair_status.json`. Historical metrics and publication markers are preserved, not revalidated.

# Reproducibility

Protocol hash and executable config are pinned in `protocol/config_hash.txt`. Regenerate with `python -m src.corrected_study` then `python -m src.validate_final_study --mode publication`. All figures and reports are generated from the run CSVs; see `metrics/final_cis.csv` and `figures/figure_index.csv` for source hashes.
