"""Locate the published signal gaps on the documented Server 2 restoration date."""

import argparse
import hashlib
from pathlib import Path
import pandas as pd


def diagnostic_channels(path, md5, cols=None):
    with path.open("rb") as handle:
        assert hashlib.file_digest(handle, "md5").hexdigest() == md5
    df = pd.read_csv(path)
    df.index = pd.to_datetime(df.pop("Timestamp"), utc=True).dt.tz_convert(
        "America/New_York"
    )
    assert df.index.is_unique
    return df if cols is None else df[cols]


def audit(zone, weather, out):
    z = diagnostic_channels(zone, "f30ea5eb154da0b8a8950c749c4b4d2d")
    w = diagnostic_channels(
        weather,
        "b4ee1f901a484bb73474a15a9f027fee",
        ["Outdoor_air_temp (°F)", "Wind_speed (m_s)", "Wind_dir (°)"],
    )
    day = z.join(w, how="outer").sort_index().loc["2024-09-12"]
    assert len(day) == 1440 and day.shape[1] == 20
    assert day.index.to_series().diff().dropna().eq(pd.Timedelta(minutes=1)).all()
    counts = day.notna().sum(axis=1)
    blank = counts.eq(0)
    rows = []
    for _, interval in day[blank].groupby((~blank).cumsum()[blank]):
        start, end = interval.index[[0, -1]]
        after = end + pd.Timedelta(minutes=1)
        rows.append(
            dict(
                start_local=start,
                end_local_inclusive=end,
                all_missing_minutes=len(interval),
                diagnostic_channels=day.shape[1],
                first_subsequent_row=after,
                channels_present_on_subsequent_row=counts.get(after),
            )
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["zone", "weather", "out"]:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    audit(args.zone, args.weather, args.out)
