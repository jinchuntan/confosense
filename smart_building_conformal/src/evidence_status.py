"""Evidence availability is separate from successful software execution."""
import json
from pathlib import Path
import pandas as pd
from .unit_checkpoint import require_cells

DATASETS = ("pleia", "pleia_energy", "rico", "bdg2")


def run_status(path, kind="core"):
    path = Path(path)
    summary = path / ("engine_summary.json" if kind == "core" else "extension_summary.json")
    if not summary.exists():
        return "missing", {}
    data = json.loads(summary.read_text(encoding="utf-8"))
    if data.get("fast", True):
        return "smoke", data
    if data.get("integration_version") != 1:
        return "historical_requires_rerun", data
    return "repaired_run_requires_scientific_validation", data


def extension_matrix(run, datasets=DATASETS, seeds=(42, 43, 44, 45, 46), n_folds=3):
    from .robustness_extension import expected_cell_names
    frames = []
    for ds in datasets:
        frame = pd.read_csv(Path(run) / ds / "robustness_cells.csv")
        require_cells(frame, ["dataset", "outer_fold", "seed", "cell"],
            [(ds, fi, seed, cell) for fi in range(n_folds) for seed in seeds
             for cell in expected_cell_names(False)])
        if not frame[["coverage_all", "mean_width", "winkler"]].notna().all().all():
            raise ValueError("missing extension measurements")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)
