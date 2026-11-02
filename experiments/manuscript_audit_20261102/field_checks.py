"""Check release contents against independent field evidence; never forward fill."""

import argparse
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd


def check(path, name, expected):
    with path.open("rb") as handle:
        actual = hashlib.file_digest(handle, name).hexdigest()
    if actual != expected:
        raise ValueError(f"Input checksum differs: {path.name}")


def housezero(source, out):
    load = source / "house_load.csv"
    solar = source / "house_solar.csv"
    check(load, "md5", "39074a2151b2b5457e1ddc0312ab2ac4")
    check(solar, "md5", "416503100cada2a29e420b095a45708a")
    a = pd.read_csv(
        load, usecols=["Timestamp", "PV_meter_1 (kW)", "PV_meter_2 (kW)"]
    ).set_index("Timestamp")
    b = pd.read_csv(solar).set_index("Timestamp")
    for table in [a, b]:
        table.index = pd.to_datetime(table.index, utc=True).tz_convert(
            "America/New_York"
        )
        assert table.index.is_unique
    d = a.join(b, how="outer").sort_index()
    d.columns = ["pv1", "pv2", "radiation"]
    dates = pd.Index(d.index.date)
    daytime = (
        (d.index.hour >= 9)
        & (d.index.hour < 16)
        & (d.radiation >= 150)
        & (d.pv1.abs() >= 0.5)
        & (d.pv2.abs() >= 0.5)
    )
    responses = daytime.groupby(dates).sum()
    output = []
    for day, night in d[d.index.hour < 3].groupby(dates[d.index.hour < 3]):
        complete = (
            len(night) == 180
            and night.index.to_series()
            .diff()
            .iloc[1:]
            .eq(pd.Timedelta(minutes=1))
            .all()
            and np.isfinite(night).all().all()
        )
        dark = night.radiation.between(0, 1).all()
        quiet = night.pv2.abs().le(0.1).all()
        before = int(responses.get(day - pd.Timedelta(days=1), 0))
        after = int(responses.get(day + pd.Timedelta(days=1), 0))
        qualifies = bool(complete and dark and quiet and min(before, after) >= 30)
        longest = np.nan
        if qualifies:
            groups = night.pv1.ne(night.pv1.shift()).cumsum()
            longest = int(groups.value_counts().max())
        output.append(
            dict(
                date=day,
                complete=complete,
                dark=dark,
                second_meter_quiet=quiet,
                daylight_minutes_before=before,
                daylight_minutes_after=after,
                qualifies=qualifies,
                target_longest_equal_run_minutes=longest,
                target_min_kw=night.pv1.min() if qualifies else np.nan,
                target_max_kw=night.pv1.max() if qualifies else np.nan,
            )
        )
    pd.DataFrame(output).to_csv(out / "housezero_controls.csv", index=False)


def csiro(source, out):
    hashes = {
        "AHU9": "d43028c46d6fadbed7f2deb749626f78be277573ead1e8b1abe8babd7515db6d",
        "AHU10": "f789b7efc5a0ec9857d5126137f727b94ad0895b63ff9b2170dd5651b26d3610",
        "fault-experiments": "b7ebad8a25baa8da7740186eb52a1eb62d0602c82dcc394ed0527ea5c6fd65f2",
    }
    for name, digest in hashes.items():
        check(source / (name + ".parquet"), "sha256", digest)
    log = pd.read_parquet(source / "fault-experiments.parquet")
    temperatures = {
        i: pd.read_parquet(source / f"AHU{i}.parquet").filter(regex="ahuZoneTemp")
        for i in (9, 10)
    }
    observations = []
    for _, row in log[
        log["Fault Name"].str.match(r"^Z[12] Temp Prx at", na=False)
    ].iterrows():
        unit = int(row.AHU)
        start, end = row["Start Datetime"], row["End Datetime"]
        expected = len(pd.date_range(start.ceil("30s"), end.floor("30s"), freq="30s"))
        data = (
            temperatures[unit].loc[start:end]
            if unit in temperatures
            else pd.DataFrame()
        )
        complete = len(data) == expected and expected > 0 and data.notna().all().all()
        match = bool(complete and (data - row["Magnitude"]).abs().le(0.05).all().any())
        observations.append(
            dict(
                unit=unit,
                start=start,
                end=end,
                setpoint_c=row.Magnitude,
                n_samples=len(data),
                expected=expected,
                complete=complete,
                any_zone_channel_held_at_setpoint=match,
            )
        )
    pd.DataFrame(observations).to_csv(out / "csiro_incidents.csv", index=False)


def korea(source, out):
    path = source / "combined_FDD.xls"
    check(path, "md5", "dff24b2453a1b787d9bf950736c3c2ac")
    data = pd.read_excel(path)
    data.Labeling.value_counts().rename("rows").to_csv(
        out / "korean_release_labels.csv", index_label="label"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("out", type=Path)
    a = p.parse_args()
    a.out.mkdir(exist_ok=True, parents=True)
    housezero(a.source, a.out)
    csiro(a.source, a.out)
    korea(a.source, a.out)
