"""PLEIAData adapter — indoor temperature and building energy consumption.

Reference
---------
Zamora-Martinez et al., PLEIAData: consumption, HVAC, temperature, weather and
motion sensor data for smart buildings. Zenodo record 7620136.

Two targets are exposed:

``temperature``
    The preliminary experiment's target, reproduced *exactly*: this adapter
    delegates to :func:`src.prepare_data.select_target` and
    :func:`src.prepare_data.build_dataset`, so the full study and the committed
    preliminary run share one code path rather than two implementations that
    could drift apart. Block B / room 11 / variable ``V2`` at 10-minute sampling.

``energy``
    The dissertation methodology also names energy consumption as a PLEIAData
    target. The authors ship per-block consumption on the same 10-minute grid as
    the room file (``consA/B/C-10T.csv``, columns ``dif_cons`` and
    ``cons_total``).

    ``dif_cons`` — energy consumed *within* each 10-minute interval — is the
    forecastable quantity. ``cons_total`` is a cumulative meter reading: it is
    near-monotonic, so persistence would score an almost perfect MAE on it and
    the comparison would be meaningless. That choice is a property of the
    channel's semantics, documented before any model is fitted, not a
    performance selection.

    Which *block* is used is likewise fixed by a documented rule rather than by
    metrics — see :func:`select_energy_block`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .. import prepare_data
from . import register
from .base import (
    ChronologicalPartitioner,
    DatasetAdapter,
    PreparedDataset,
    PreparedSeries,
    Provenance,
    file_checksum,
)

ENERGY_BLOCKS = ("A", "B", "C")


def select_energy_block(cfg: dict, interim: Path) -> tuple[str, pd.DataFrame]:
    """Pick the consumption block by a documented, performance-independent rule.

    Every block is profiled first (rows, coverage, variability, negative-reading
    count) so the audit file shows what was rejected and why. The default rule,
    ``match_temperature_block``, takes the block that houses the preliminary
    temperature target, which keeps the two PLEIAData targets in the same part of
    the building and makes the pairing interpretable. No forecast is run during
    selection.
    """
    ecfg = cfg.get("energy", {})
    rule = ecfg.get("block_rule", "match_temperature_block")
    preferred = str(ecfg.get("block", "B")).upper()
    pattern = ecfg.get("file_pattern", "Data_Nature/processed_data/cons{block}-10T.csv")
    value_col = ecfg.get("value_col", "dif_cons")
    sep = cfg["dataset"].get("csv_sep", ";")

    rows = []
    frames: dict[str, pd.DataFrame] = {}
    for block in ENERGY_BLOCKS:
        path = interim / pattern.format(block=block)
        if not path.exists():
            rows.append({"block": block, "file": str(path), "available": False,
                         "reason_excluded": "file not present in the archive"})
            continue
        df = pd.read_csv(path, sep=sep)
        df["Date"] = pd.to_datetime(df["Date"], utc=True, format="mixed")
        df["Date"] = df["Date"].dt.tz_convert("UTC").dt.tz_localize(None)
        df = df.sort_values("Date").set_index("Date")
        frames[block] = df
        v = df[value_col].astype(float)
        span = (df.index.max() - df.index.min())
        expected = int(span / pd.Timedelta("10min")) + 1
        rows.append({
            "block": block, "file": str(path), "available": True,
            "value_col": value_col,
            "n_rows": len(df), "n_valid": int(v.notna().sum()),
            "coverage": round(float(v.notna().sum()) / expected, 5) if expected else 0.0,
            "start": df.index.min(), "end": df.index.max(),
            "mean": round(float(v.mean()), 4), "std": round(float(v.std()), 4),
            "min": round(float(v.min()), 4), "max": round(float(v.max()), 4),
            "n_negative": int((v < 0).sum()),
            "reason_excluded": "",
        })

    audit = pd.DataFrame(rows)
    usable = audit[audit.get("available", False) == True]  # noqa: E712
    if usable.empty:
        raise FileNotFoundError(
            "no PLEIAData consumption file found; expected e.g. "
            f"{interim / pattern.format(block='B')}"
        )

    if rule == "match_temperature_block" and preferred in set(usable["block"]):
        chosen = preferred
        reason = (
            f"Block {preferred} houses the preliminary indoor-temperature target "
            "(block B, room 11, V2), so the energy target is taken from the same "
            "block to keep the two PLEIAData targets comparable. Rule fixed "
            "before any model was fitted; no forecast metric consulted."
        )
    else:
        # Deterministic fallback: most complete series, ties broken by block id.
        ranked = usable.sort_values(["coverage", "n_valid", "block"],
                                    ascending=[False, False, True])
        chosen = str(ranked.iloc[0]["block"])
        reason = ("Highest-coverage consumption block, with the block identifier as "
                  "a deterministic tie-break. No forecast metric consulted.")

    audit["selected"] = audit["block"] == chosen
    audit["selection_rule"] = rule
    audit["selection_reason"] = ""
    audit.loc[audit["selected"], "selection_reason"] = reason
    audit["target_column_rationale"] = (
        f"'{value_col}' is the per-interval consumption increment; 'cons_total' is a "
        "cumulative meter reading and is excluded because its near-monotonicity "
        "makes persistence trivially accurate and the comparison uninformative."
    )
    return chosen, audit


@register
class PleiaAdapter(DatasetAdapter):
    dataset_id = "pleia"

    def provenance(self) -> Provenance:
        return Provenance(
            dataset_id=self.dataset_id,
            official_source="Zenodo record 7620136",
            doi="10.5281/zenodo.7620136",
            download_url="https://zenodo.org/records/7620136",
            archive_name="Data_Nature",
            license="see the Zenodo record",
            citation=(
                "Zamora-Martinez, F. et al. PLEIAData: consumption, HVAC, temperature, "
                "weather and motion sensor data for smart buildings. Zenodo, 2023."
            ),
        )

    # ------------------------------------------------------------------ #
    def prepare(self, cfg: dict) -> PreparedDataset:
        target_kind = cfg.get("target_kind", "temperature")
        if target_kind == "temperature":
            return self._prepare_temperature(cfg)
        if target_kind == "energy":
            return self._prepare_energy(cfg)
        raise ValueError(f"unknown PLEIAData target_kind {target_kind!r}")

    # ------------------------------------------------------------------ #
    def _provenance_with_file(self, path: Path) -> Provenance:
        prov = self.provenance()
        if path.exists():
            prov.archive_name = path.name
            prov.checksum = file_checksum(path)
        return prov

    def _partitioner(self, cfg: dict) -> ChronologicalPartitioner:
        split = cfg.get("split", {})
        tr = split.get("train_frac", 0.6)
        ca = split.get("calib_frac", 0.2)
        return ChronologicalPartitioner(fractions=(tr, ca, 1.0 - tr - ca))

    # ------------------------------------------------------------------ #
    def _prepare_temperature(self, cfg: dict) -> PreparedDataset:
        """Delegate to the preliminary pipeline so both studies share one path."""
        df = prepare_data.load_room_table(cfg)
        choice, audit = prepare_data.select_target(df, cfg)
        processed = prepare_data.build_dataset(df, choice, cfg)

        cov = cfg["covariates"]
        covariates = [cov["outdoor_temp"], cov["humidity"], cov["radiation"],
                      cov["hvac_state"], cov["setpoint"], *cov["hvac_mode_onehot"]]
        covariates = [c for c in covariates if c in processed.columns]

        series = PreparedSeries(
            dataset_id=self.dataset_id,
            target_id=f"{choice['block']}-room{choice['room']}-{choice['sensor_variable']}",
            frame=processed,
            freq=pd.Timedelta(cfg["resample"]["freq"]),
            group_id=None,
            season_steps=cfg["resample"]["season_steps"],
            covariates=covariates,
            units="degC",
            metadata={"block": choice["block"], "room": choice["room"],
                      "variable": choice["sensor_variable"]},
        )
        path = Path(cfg["paths"]["interim_dir"]) / cfg["dataset"]["room_all_file"]
        prov = self._provenance_with_file(path)
        prov.preprocessing = [
            f"physically implausible values outside "
            f"[{cfg['outliers']['target_min']}, {cfg['outliers']['target_max']}] degC removed",
            f"gaps up to {cfg['missing']['max_short_gap_steps']} steps interpolated in time",
            f"resampled onto a regular {cfg['resample']['freq']} grid",
        ]
        return PreparedDataset(
            dataset_id=self.dataset_id, series=[series],
            partitioner=self._partitioner(cfg), provenance=prov,
            target_description=(
                f"PLEIAData indoor temperature, block {choice['block']} room "
                f"{choice['room']} variable {choice['sensor_variable']}"
            ),
            metadata={"target_kind": "temperature", "selection_audit": audit,
                      "choice": choice},
        )

    # ------------------------------------------------------------------ #
    def _prepare_energy(self, cfg: dict) -> PreparedDataset:
        interim = Path(cfg["paths"]["interim_dir"])
        ecfg = cfg.get("energy", {})
        value_col = ecfg.get("value_col", "dif_cons")
        block, audit = select_energy_block(cfg, interim)

        pattern = ecfg.get("file_pattern", "Data_Nature/processed_data/cons{block}-10T.csv")
        path = interim / pattern.format(block=block)
        df = pd.read_csv(path, sep=cfg["dataset"].get("csv_sep", ";"))
        df["Date"] = pd.to_datetime(df["Date"], utc=True, format="mixed")
        df["Date"] = df["Date"].dt.tz_convert("UTC").dt.tz_localize(None)
        df = df.sort_values("Date").drop_duplicates("Date").set_index("Date")

        freq = pd.Timedelta(cfg["resample"]["freq"])
        grid = pd.date_range(df.index.min(), df.index.max(), freq=freq)
        df = df.reindex(grid)
        df.index.name = "timestamp"

        target = df[value_col].astype(float)
        # A negative interval increment can only be a meter reset or rollover, so
        # it is treated as corrupt rather than clipped to zero.
        n_negative = int((target < 0).sum())
        target = target.mask(target < 0)
        hi = ecfg.get("max_value")
        n_high = 0
        if hi is not None:
            n_high = int((target > hi).sum())
            target = target.mask(target > hi)

        out = pd.DataFrame(index=grid)
        out.index.name = "timestamp"
        out["target_was_missing"] = target.isna().astype(int)
        max_gap = cfg["missing"]["max_short_gap_steps"]
        out["target"] = target.interpolate(method="time", limit=max_gap, limit_area="inside")

        # Weather covariates on the same grid, when the authors' file is present.
        covariates: list[str] = []
        wpath = interim / ecfg.get(
            "weather_file", "Data_Nature/processed_data/data-weather-10T.csv"
        )
        if wpath.exists():
            w = pd.read_csv(wpath, sep=cfg["dataset"].get("csv_sep", ";"))
            tcol = "Date" if "Date" in w.columns else w.columns[0]
            w[tcol] = pd.to_datetime(w[tcol], utc=True, format="mixed")
            w[tcol] = w[tcol].dt.tz_convert("UTC").dt.tz_localize(None)
            w = w.sort_values(tcol).drop_duplicates(tcol).set_index(tcol).reindex(grid)
            for col in ecfg.get("weather_covariates", ["tmed", "hrmed", "radmed"]):
                if col in w.columns:
                    s = w[col].astype(float)
                    out[f"{col}_was_missing"] = s.isna().astype(int)
                    out[col] = s.interpolate(method="time", limit=max_gap, limit_area="inside")
                    covariates.append(col)

        series = PreparedSeries(
            dataset_id=self.dataset_id,
            target_id=f"block{block}-{value_col}",
            frame=out,
            freq=freq,
            group_id=None,
            season_steps=cfg["resample"]["season_steps"],
            covariates=covariates,
            units="kWh per interval",
            metadata={"block": block, "value_col": value_col},
        )
        prov = self._provenance_with_file(path)
        prov.preprocessing = [
            f"target '{value_col}' (per-interval consumption increment) from block {block}",
            f"{n_negative} negative increments masked as meter resets",
            f"{n_high} values above the configured ceiling masked" if hi is not None else "",
            f"gaps up to {max_gap} steps interpolated in time",
        ]
        prov.preprocessing = [p for p in prov.preprocessing if p]
        prov.notes.append(
            "cons_total (cumulative meter) deliberately not used as a target: it is "
            "near-monotonic and would make persistence trivially accurate."
        )
        return PreparedDataset(
            dataset_id=self.dataset_id, series=[series],
            partitioner=self._partitioner(cfg), provenance=prov,
            target_description=f"PLEIAData block {block} interval energy consumption ({value_col})",
            metadata={"target_kind": "energy", "selection_audit": audit,
                      "n_negative_masked": n_negative},
        )
