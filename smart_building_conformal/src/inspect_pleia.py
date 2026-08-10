"""Recursively profile every extracted PLEIAData file.

Produces ``outputs/data_profiles/file_inventory.csv`` describing, for each file,
its format, shape, candidate timestamp / identifier columns, numeric variables,
missingness and observed time range. No file name or schema is assumed in
advance; the profiler discovers everything from the data itself.
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from pathlib import Path

import pandas as pd

TABULAR_SUFFIXES = {".csv", ".txt", ".tsv", ".parquet", ".pq", ".xlsx", ".xls"}
TIME_NAME_HINTS = ("time", "date", "timestamp", "datetime", "fecha", "hora")
ID_NAME_HINTS = ("id", "sensor", "room", "device", "name", "block", "zone", "meter")


def sniff_separator(path: Path) -> str:
    """Guess the delimiter of a text table from its first non-empty lines."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        # Fall back to whichever common delimiter appears most often.
        counts = {d: sample.count(d) for d in [",", ";", "\t", "|"]}
        return max(counts, key=counts.get)


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    sep = sniff_separator(path)
    return pd.read_csv(path, sep=sep, low_memory=False)


def detect_timestamp_columns(df: pd.DataFrame) -> list[str]:
    candidates: list[str] = []
    for col in df.columns:
        lower = str(col).lower()
        already_dt = pd.api.types.is_datetime64_any_dtype(df[col])
        name_hint = any(h in lower for h in TIME_NAME_HINTS)
        parses = False
        if not already_dt and df[col].dtype == object:
            sample = df[col].dropna().head(200)
            if len(sample):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
                parses = parsed.notna().mean() > 0.9
        if already_dt or name_hint or parses:
            candidates.append(str(col))
    return candidates


def detect_identifier_columns(df: pd.DataFrame) -> list[str]:
    candidates: list[str] = []
    n = max(1, len(df))
    for col in df.columns:
        lower = str(col).lower()
        name_hint = any(h in lower for h in ID_NAME_HINTS)
        low_card = df[col].dtype == object and df[col].nunique(dropna=True) <= max(50, 0.05 * n)
        if name_hint or low_card:
            candidates.append(str(col))
    return candidates


def time_range(df: pd.DataFrame, ts_cols: list[str]) -> tuple[str, str, str]:
    for col in ts_cols:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
            if parsed.notna().any():
                return col, str(parsed.min()), str(parsed.max())
        except Exception:
            continue
    return "", "", ""


def profile_file(path: Path, root: Path) -> dict:
    rel = str(path.relative_to(root))
    suffix = path.suffix.lower()
    info: dict = {
        "file": rel,
        "format": suffix.lstrip("."),
        "size_mb": round(path.stat().st_size / 1e6, 3),
        "n_rows": "",
        "n_cols": "",
        "timestamp_columns": "",
        "identifier_columns": "",
        "numeric_columns": "",
        "missing_fraction": "",
        "min_timestamp": "",
        "max_timestamp": "",
        "primary_timestamp_column": "",
        "note": "",
    }
    if suffix not in TABULAR_SUFFIXES:
        info["note"] = "non-tabular; not profiled as a table"
        return info
    try:
        df = read_table(path)
    except Exception as exc:  # pragma: no cover - defensive
        info["note"] = f"read error: {exc}"
        return info

    ts_cols = detect_timestamp_columns(df)
    id_cols = detect_identifier_columns(df)
    num_cols = [str(c) for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    primary_ts, tmin, tmax = time_range(df, ts_cols)

    total_cells = df.shape[0] * df.shape[1]
    missing = float(df.isna().sum().sum() / total_cells) if total_cells else 0.0

    info.update(
        n_rows=int(df.shape[0]),
        n_cols=int(df.shape[1]),
        timestamp_columns="; ".join(ts_cols),
        identifier_columns="; ".join(id_cols),
        numeric_columns="; ".join(num_cols),
        missing_fraction=round(missing, 5),
        min_timestamp=tmin,
        max_timestamp=tmax,
        primary_timestamp_column=primary_ts,
    )
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile the extracted PLEIAData files.")
    parser.add_argument("--interim-dir", default="data/interim")
    parser.add_argument("--out", default="outputs/data_profiles/file_inventory.csv")
    args = parser.parse_args()

    root = Path(args.interim_dir)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files:
        raise SystemExit(f"No files found under {root}. Run download_data.py first.")

    rows = []
    for path in files:
        print(f"[profile] {path.relative_to(root)}")
        rows.append(profile_file(path, root))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"[done] wrote inventory for {len(rows)} files to {out_path}")

    # A compact machine-readable copy is convenient for downstream steps.
    with open(out_path.with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, default=str)


if __name__ == "__main__":
    main()
