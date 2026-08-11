"""Building Data Genome Project 2 adapter — cross-building energy benchmark.

Reference
---------
Miller, C. et al. (2020). "The Building Data Genome Project 2, energy meter data
from the ASHRAE Great Energy Predictor III competition." *Scientific Data*, 7,
368. DOI: 10.1038/s41597-020-00712-x

Source
------
The authors' own repository, ``buds-lab/building-data-genome-project-2``. The CSV
files are stored with Git LFS, so the raw ``raw.githubusercontent.com`` path
serves a 130-byte pointer rather than the data; this adapter uses the LFS media
endpoint (``media.githubusercontent.com/media/...``), which returns the real
files. No third-party mirror is used.

Target
------
Hourly whole-building **electricity** consumption (``electricity.csv``, one column
per building, kWh). Sampling is verified from the data rather than assumed.

Subset selection
----------------
:func:`select_subset` picks the buildings, and it is deliberately blind to
forecasting performance — no model is fitted, and no error metric exists, at the
point it runs. It filters on the metadata and on data-quality facts only
(electricity meter present, long enough common period, completeness, non-constant
series, documented primary use), ranks the survivors by a deterministic key, and
caps how many may come from any one site so the sample spans several campuses
rather than clustering in the largest one. Ties break on ``building_id``, so the
result is reproducible without needing a random seed at all.

Every candidate — selected or not — is written to
``data_profiles/subset_selection.csv`` with the reason it was kept or dropped.

Independence
------------
Each building becomes its own :class:`~src.datasets.base.PreparedSeries`, so
feature windows never cross a building boundary, and each building receives its
own chronological train / calibration / test split via
:class:`~src.datasets.base.ChronologicalPartitioner`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import register
from .base import (
    ChronologicalPartitioner,
    DatasetAdapter,
    PreparedDataset,
    PreparedSeries,
    Provenance,
    file_checksum,
)

LFS_BASE = ("https://media.githubusercontent.com/media/buds-lab/"
            "building-data-genome-project-2/master/")
FILES = {
    "metadata.csv": "data/metadata/metadata.csv",
    "electricity.csv": "data/meters/raw/electricity.csv",
    "weather.csv": "data/weather/weather.csv",
}


def download(raw_dir: Path, names: list[str] | None = None) -> dict[str, Path]:
    """Fetch the BDG2 CSVs from the authors' repository via the Git LFS endpoint."""
    import requests

    raw_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, rel in FILES.items():
        if names and name not in names:
            continue
        dest = raw_dir / name
        with requests.get(LFS_BASE + rel, stream=True, timeout=3600) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            if dest.exists() and dest.stat().st_size == total:
                out[name] = dest
                continue
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(1 << 20):
                    f.write(chunk)
        out[name] = dest
    return out


# --------------------------------------------------------------------------- #
# Subset selection
# --------------------------------------------------------------------------- #
def profile_buildings(
    meters: pd.DataFrame,
    metadata: pd.DataFrame,
    freq: pd.Timedelta,
) -> pd.DataFrame:
    """One quality row per building column in the meter file."""
    meta = metadata.set_index("building_id") if "building_id" in metadata.columns else metadata
    rows = []
    for col in meters.columns:
        s = meters[col].astype(float)
        observed = s.dropna()
        if observed.empty:
            rows.append({"building_id": col, "n_valid": 0, "coverage": 0.0,
                         "missing_fraction": 1.0, "std": np.nan,
                         "start": pd.NaT, "end": pd.NaT, "span_days": 0.0,
                         "n_negative": 0, "site_id": meta["site_id"].get(col, ""),
                         "primary_use": meta["primaryspaceusage"].get(col, ""),
                         "sqm": meta["sqm"].get(col, np.nan)})
            continue
        start, end = observed.index[0], observed.index[-1]
        expected = int((end - start) / freq) + 1
        rows.append({
            "building_id": col,
            "site_id": meta["site_id"].get(col, "") if "site_id" in meta else "",
            "primary_use": meta["primaryspaceusage"].get(col, "") if "primaryspaceusage" in meta else "",
            "sub_primary_use": meta["sub_primaryspaceusage"].get(col, "") if "sub_primaryspaceusage" in meta else "",
            "sqm": float(meta["sqm"].get(col, np.nan)) if "sqm" in meta else np.nan,
            "year_built": meta["yearbuilt"].get(col, np.nan) if "yearbuilt" in meta else np.nan,
            "meter_type": "electricity",
            "start": start, "end": end,
            "span_days": float((end - start) / pd.Timedelta(days=1)),
            "n_valid": int(len(observed)),
            "coverage": float(len(observed) / expected) if expected else 0.0,
            "missing_fraction": float(1.0 - len(observed) / expected) if expected else 1.0,
            "mean": float(observed.mean()), "std": float(observed.std()),
            "min": float(observed.min()), "max": float(observed.max()),
            "n_negative": int((observed < 0).sum()),
            "n_zero": int((observed == 0).sum()),
            "constant_fraction": float((observed.diff() == 0).mean()),
        })
    return pd.DataFrame(rows)


def select_subset(profile: pd.DataFrame, sel: dict) -> pd.DataFrame:
    """Apply the documented, metric-free selection rule.

    Returns ``profile`` with ``selected``, ``selection_rank`` and
    ``selection_reason`` columns added for *every* candidate.
    """
    n_target = int(sel.get("n_buildings", 10))
    min_days = float(sel.get("min_span_days", 300))
    min_cov = float(sel.get("min_coverage", 0.95))
    max_const = float(sel.get("max_constant_fraction", 0.5))
    max_per_site = int(sel.get("max_per_site", 2))
    require_use = bool(sel.get("require_documented_use", True))

    df = profile.copy()
    reasons = []
    for _, r in df.iterrows():
        why = []
        if r["n_valid"] == 0:
            why.append("no observations")
        if r["span_days"] < min_days:
            why.append(f"span {r['span_days']:.0f} d < {min_days:.0f} d")
        if r["coverage"] < min_cov:
            why.append(f"coverage {r['coverage']:.3f} < {min_cov}")
        if not np.isfinite(r.get("std", np.nan)) or r.get("std", 0) <= 0:
            why.append("constant or undefined series")
        if r.get("constant_fraction", 0) > max_const:
            why.append(f"constant_fraction {r['constant_fraction']:.2f} > {max_const}")
        if r.get("n_negative", 0) > 0:
            why.append(f"{int(r['n_negative'])} negative readings")
        if require_use and not str(r.get("primary_use", "")).strip():
            why.append("no documented primary use")
        reasons.append("; ".join(why))
    df["reason_excluded"] = reasons
    df["eligible"] = df["reason_excluded"] == ""

    # Deterministic ranking: most complete, then longest, then id. No seed needed.
    ranked = df[df["eligible"]].sort_values(
        by=["missing_fraction", "span_days", "n_valid", "building_id"],
        ascending=[True, False, False, True],
    )

    chosen, per_site = [], {}
    for _, r in ranked.iterrows():
        site = str(r.get("site_id", ""))
        if per_site.get(site, 0) >= max_per_site:
            continue
        chosen.append(r["building_id"])
        per_site[site] = per_site.get(site, 0) + 1
        if len(chosen) >= n_target:
            break
    # If the per-site cap starved the sample, top it up in strict rank order.
    if len(chosen) < n_target:
        for _, r in ranked.iterrows():
            if r["building_id"] not in chosen:
                chosen.append(r["building_id"])
            if len(chosen) >= n_target:
                break

    order = {b: i for i, b in enumerate(chosen)}
    df["selected"] = df["building_id"].isin(chosen)
    df["selection_rank"] = df["building_id"].map(order)
    df["selection_reason"] = ""
    df.loc[df["selected"], "selection_reason"] = (
        f"eligible (span >= {min_days:.0f} d, coverage >= {min_cov}, non-constant, "
        f"no negative readings, documented use) and within the top {n_target} by "
        f"(missing_fraction asc, span desc, building_id asc) under a cap of "
        f"{max_per_site} buildings per site. No forecast metric was used."
    )
    df.loc[~df["selected"] & df["eligible"], "selection_reason"] = (
        "eligible but outside the configured subset size or site cap"
    )
    df.loc[~df["eligible"], "selection_reason"] = df.loc[~df["eligible"], "reason_excluded"]
    return df.sort_values(["selected", "selection_rank", "building_id"],
                          ascending=[False, True, True])


# --------------------------------------------------------------------------- #
# Adapter
# --------------------------------------------------------------------------- #
@register
class Bdg2Adapter(DatasetAdapter):
    dataset_id = "bdg2"

    def provenance(self) -> Provenance:
        return Provenance(
            dataset_id=self.dataset_id,
            official_source="buds-lab/building-data-genome-project-2 (authors' repository)",
            doi="10.1038/s41597-020-00712-x",
            download_url=LFS_BASE + FILES["electricity.csv"],
            license="MIT (repository); see the paper for data terms",
            citation=(
                "Miller, C. et al. (2020). The Building Data Genome Project 2, energy "
                "meter data from the ASHRAE Great Energy Predictor III competition. "
                "Scientific Data, 7, 368."
            ),
        )

    def prepare(self, cfg: dict) -> PreparedDataset:
        bcfg = cfg.get("bdg2", {})
        raw_dir = Path(cfg["paths"]["raw_dir"]) / bcfg.get("subdir", "bdg2")
        meter_path = raw_dir / "electricity.csv"
        meta_path = raw_dir / "metadata.csv"
        if not meter_path.exists() or not meta_path.exists():
            if bcfg.get("auto_download", True):
                download(raw_dir, names=["electricity.csv", "metadata.csv"])
            if not meter_path.exists():
                raise FileNotFoundError(
                    f"BDG2 electricity.csv not found under {raw_dir}; run "
                    "`python -m src.fetch_datasets --dataset bdg2` first"
                )

        meters = pd.read_csv(meter_path, parse_dates=["timestamp"])
        meters = meters.sort_values("timestamp").set_index("timestamp")
        meters = meters[~meters.index.duplicated(keep="first")]
        metadata = pd.read_csv(meta_path, low_memory=False)

        # Verify the sampling interval rather than assuming hourly.
        deltas = meters.index.to_series().diff().dropna()
        freq = pd.Timedelta(deltas.mode().iloc[0]) if len(deltas) else pd.Timedelta("1h")
        configured = bcfg.get("freq")
        if configured and pd.Timedelta(configured) != freq:
            raise ValueError(
                f"configured BDG2 freq {configured} does not match the observed "
                f"modal sampling interval {freq}"
            )

        profile = profile_buildings(meters, metadata, freq)
        selection = select_subset(profile, bcfg.get("selection", {}))
        chosen = selection[selection["selected"]].sort_values("selection_rank")

        max_gap = cfg.get("missing", {}).get("max_short_gap_steps", 3)
        season_steps = int(bcfg.get("season_steps", 24))  # daily cycle at 1 h

        # Optional per-site weather covariates.
        weather = None
        wpath = raw_dir / "weather.csv"
        if bcfg.get("use_weather", True) and wpath.exists():
            weather = pd.read_csv(wpath, parse_dates=["timestamp"])

        series_list = []
        for _, row in chosen.iterrows():
            bid = row["building_id"]
            s = meters[bid].astype(float)
            s = s.loc[s.first_valid_index(): s.last_valid_index()]
            grid = pd.date_range(s.index[0], s.index[-1], freq=freq)
            s = s.reindex(grid)

            out = pd.DataFrame(index=grid)
            out.index.name = "timestamp"
            out["target_was_missing"] = s.isna().astype(int)
            out["target"] = s.interpolate(method="time", limit=max_gap, limit_area="inside")

            covariates: list[str] = []
            if weather is not None and "site_id" in weather.columns:
                w = weather[weather["site_id"] == row.get("site_id")]
                if len(w):
                    w = (w.sort_values("timestamp").drop_duplicates("timestamp")
                         .set_index("timestamp").reindex(grid))
                    for col in bcfg.get("weather_covariates",
                                        ["airTemperature", "dewTemperature"]):
                        if col in w.columns and w[col].notna().any():
                            v = w[col].astype(float)
                            out[f"{col}_was_missing"] = v.isna().astype(int)
                            out[col] = v.interpolate(method="time", limit=max_gap,
                                                     limit_area="inside")
                            covariates.append(col)

            series_list.append(PreparedSeries(
                dataset_id=self.dataset_id,
                target_id="electricity",
                frame=out,
                freq=freq,
                group_id=str(bid),
                season_steps=season_steps,
                covariates=covariates,
                units="kWh",
                metadata={"site_id": row.get("site_id"),
                          "primary_use": row.get("primary_use"),
                          "sqm": row.get("sqm")},
            ))

        if not series_list:
            raise RuntimeError("BDG2 subset selection returned no buildings")

        # Concatenation requires one schema; intersect the covariate sets.
        common = set(series_list[0].covariates)
        for s in series_list:
            common &= set(s.covariates)
        ordered = [c for c in series_list[0].covariates if c in common]
        for s in series_list:
            keep = ["target", "target_was_missing"] + ordered
            keep += [f"{c}_was_missing" for c in ordered if f"{c}_was_missing" in s.frame.columns]
            s.frame = s.frame[[c for c in keep if c in s.frame.columns]]
            s.covariates = list(ordered)

        split = cfg["split"]
        partitioner = ChronologicalPartitioner(
            fractions=(split["train_frac"], split["calib_frac"],
                       1.0 - split["train_frac"] - split["calib_frac"])
        )

        prov = self.provenance()
        prov.archive_name = "electricity.csv, metadata.csv"
        prov.checksum = f"electricity={file_checksum(meter_path)[:16]};meta={file_checksum(meta_path)[:16]}"
        prov.preprocessing = [
            f"observed modal sampling interval {freq}",
            f"subset of {len(series_list)} buildings selected by documented "
            "quality criteria only (see subset_selection.csv)",
            f"gaps up to {max_gap} steps interpolated within a building only",
            "each building split chronologically into train/calibration/test",
        ]

        return PreparedDataset(
            dataset_id=self.dataset_id,
            series=series_list,
            partitioner=partitioner,
            provenance=prov,
            target_description="BDG2 hourly whole-building electricity consumption (kWh)",
            metadata={
                "target_kind": "energy",
                "subset_selection": selection,
                "n_candidates": len(profile),
                "n_selected": len(series_list),
                "observed_freq": str(freq),
                "season_steps": season_steps,
            },
        )
