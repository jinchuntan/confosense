# Reproducibility

Protocol hash and executable config are pinned in `protocol/config_hash.txt`. Regenerate with `python -m src.corrected_study` then `python -m src.validate_final_study --mode publication`. All figures and reports are generated from the run CSVs; see `metrics/final_cis.csv` and `figures/figure_index.csv` for source hashes.
