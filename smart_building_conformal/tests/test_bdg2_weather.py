"""BDG2 configured weather must be present or fail loudly (audit B3).

Configured weather covariates are never silently dropped: if weather is
configured but the file is absent, the adapter raises (or, only when
``weather_optional: true`` is set, proceeds weatherless and records the status).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.datasets.bdg2 import Bdg2Adapter


def _write_fixture(raw_dir, with_weather):
    raw_dir.mkdir(parents=True, exist_ok=True)
    idx = pd.date_range("2021-01-01", periods=400, freq="1h")
    rng = np.random.default_rng(0)
    meters = pd.DataFrame({"timestamp": idx,
                           "bldgA": 100 + rng.normal(0, 5, len(idx)),
                           "bldgB": 200 + rng.normal(0, 8, len(idx))})
    meters.to_csv(raw_dir / "electricity.csv", index=False)
    pd.DataFrame({
        "building_id": ["bldgA", "bldgB"],
        "site_id": ["siteX", "siteX"],
        "primaryspaceusage": ["Office", "Office"],
        "sqm": [1000.0, 2000.0],
    }).to_csv(raw_dir / "metadata.csv", index=False)
    if with_weather:
        pd.DataFrame({"timestamp": idx, "site_id": "siteX",
                      "airTemperature": rng.normal(15, 5, len(idx)),
                      "dewTemperature": rng.normal(8, 3, len(idx))}
                     ).to_csv(raw_dir / "weather.csv", index=False)


def _cfg(raw_dir, use_weather=True, weather_optional=False):
    return {
        "paths": {"raw_dir": str(raw_dir.parent)},
        "split": {"train_frac": 0.6, "calib_frac": 0.2},
        "missing": {"max_short_gap_steps": 3},
        "bdg2": {
            "subdir": raw_dir.name, "freq": "1h", "season_steps": 24,
            "auto_download": False, "use_weather": use_weather,
            "weather_optional": weather_optional,
            "weather_covariates": ["airTemperature", "dewTemperature"],
            "selection": {"n_buildings": 2, "min_span_days": 5,
                          "min_coverage": 0.5, "max_constant_fraction": 0.9,
                          "max_per_site": 2, "require_documented_use": False},
        },
    }


def test_configured_weather_missing_raises_loudly(tmp_path):
    raw = tmp_path / "bdg2"
    _write_fixture(raw, with_weather=False)
    with pytest.raises(FileNotFoundError, match="weather is configured"):
        Bdg2Adapter().prepare(_cfg(raw, use_weather=True, weather_optional=False))


def test_weather_optional_proceeds_and_records_status(tmp_path):
    raw = tmp_path / "bdg2"
    _write_fixture(raw, with_weather=False)
    prepared = Bdg2Adapter().prepare(
        _cfg(raw, use_weather=True, weather_optional=True))
    assert prepared.metadata["weather_status"] == \
        "configured_missing_proceeding_weatherless"


def test_weather_present_is_loaded_and_used(tmp_path):
    raw = tmp_path / "bdg2"
    _write_fixture(raw, with_weather=True)
    prepared = Bdg2Adapter().prepare(_cfg(raw, use_weather=True))
    assert prepared.metadata["weather_status"] == "loaded"
    assert prepared.metadata["n_buildings_with_weather"] >= 1
