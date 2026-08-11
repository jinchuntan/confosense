"""Download the full-study datasets from their official sources.

Kept separate from the experiment drivers so that a run never silently blocks on
a multi-hundred-megabyte transfer, and so a failed download is reported as a
download failure rather than as a missing-data error deep inside a pipeline.

Transfers are resumable. Both Zenodo and the GitHub LFS endpoint occasionally cut
a long connection mid-stream (which is exactly what happened while developing
this), so each file is fetched with byte-range resume and bounded retries, then
size-verified before being accepted.

Usage
-----
    python -m src.fetch_datasets --dataset rico
    python -m src.fetch_datasets --dataset bdg2
    python -m src.fetch_datasets --all

PLEIAData has its own long-standing downloader, :mod:`src.download_data`, which
this module leaves untouched.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import requests

from .datasets import bdg2 as bdg2_mod
from .datasets import rico as rico_mod


def fetch(url: str, dest: Path, expected_size: int | None = None,
          retries: int = 6, chunk: int = 1 << 20) -> Path:
    """Download ``url`` to ``dest``, resuming from a partial file if present."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retries + 1):
        have = dest.stat().st_size if dest.exists() else 0
        if expected_size is not None and have == expected_size:
            print(f"[skip] {dest.name} complete ({have/1e6:.1f} MB)")
            return dest
        if expected_size is not None and have > expected_size:
            dest.unlink()          # corrupt/overlong partial; start over
            have = 0

        headers = {"Range": f"bytes={have}-"} if have else {}
        mode = "ab" if have else "wb"
        try:
            with requests.get(url, headers=headers, stream=True, timeout=600) as r:
                if have and r.status_code == 200:
                    # Server ignored the range request; restart cleanly.
                    mode, have = "wb", 0
                elif have and r.status_code != 206:
                    r.raise_for_status()
                else:
                    r.raise_for_status()
                with open(dest, mode) as f:
                    for block in r.iter_content(chunk):
                        f.write(block)
            size = dest.stat().st_size
            if expected_size is None or size == expected_size:
                print(f"[done] {dest.name} ({size/1e6:.1f} MB)")
                return dest
            print(f"[warn] {dest.name} is {size} bytes, expected {expected_size}; retrying")
        except (requests.RequestException, OSError) as exc:
            print(f"[retry {attempt}/{retries}] {dest.name}: {type(exc).__name__}: {exc}")
        time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f"failed to download {url} after {retries} attempts")


def fetch_rico(raw_dir: Path) -> list[Path]:
    meta = requests.get(
        rico_mod.ZENODO_API.format(record=rico_mod.ZENODO_RECORD), timeout=120
    ).json()
    out = []
    for f in meta.get("files", []):
        out.append(fetch(f["links"]["self"], raw_dir / f["key"], f.get("size")))
    return out


def fetch_bdg2(raw_dir: Path, names: list[str] | None = None) -> list[Path]:
    out = []
    for name, rel in bdg2_mod.FILES.items():
        if names and name not in names:
            continue
        url = bdg2_mod.LFS_BASE + rel
        head = requests.head(url, timeout=120, allow_redirects=True)
        size = int(head.headers.get("content-length", 0)) or None
        out.append(fetch(url, raw_dir / name, size))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch ConfoSense full-study datasets.")
    p.add_argument("--dataset", choices=["rico", "bdg2"], action="append", default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("--raw-dir", default="data/raw")
    args = p.parse_args()

    wanted = set(args.dataset or [])
    if args.all or not wanted:
        wanted = {"rico", "bdg2"}

    raw = Path(args.raw_dir)
    if "rico" in wanted:
        print("== RICO (Zenodo 14871584) ==")
        fetch_rico(raw / "rico")
    if "bdg2" in wanted:
        print("== BDG2 (buds-lab repository, Git LFS) ==")
        fetch_bdg2(raw / "bdg2")


if __name__ == "__main__":
    main()
