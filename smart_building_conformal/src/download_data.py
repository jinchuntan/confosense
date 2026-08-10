"""Download and extract the PLEIAData dataset from its official Zenodo record.

The script is idempotent: an already-downloaded archive with a matching size is
not re-fetched, and extraction is skipped if the target directory already holds
files. Nothing about the internal file names or structure is assumed here; that
is left to :mod:`src.inspect_pleia`.

Reference record: https://zenodo.org/records/7620136
"""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

import requests

ZENODO_API = "https://zenodo.org/api/records/{record_id}"
DEFAULT_RECORD_ID = "7620136"


def fetch_record_metadata(record_id: str) -> dict:
    resp = requests.get(ZENODO_API.format(record_id=record_id), timeout=60)
    resp.raise_for_status()
    return resp.json()


def md5_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def download_file(url: str, dest: Path, expected_size: int | None = None) -> None:
    if dest.exists() and expected_size is not None and dest.stat().st_size == expected_size:
        print(f"[skip] {dest.name} already present with expected size")
        return
    print(f"[get ] {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=900) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        done = 0
        step = max(1, total // 20) if total else 0
        next_mark = step
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                if step and done >= next_mark:
                    print(f"       {done / 1e6:8.1f} / {total / 1e6:.1f} MB")
                    next_mark += step
    print(f"[done] saved {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def extract_zip(archive: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = [p for p in out_dir.rglob("*") if p.is_file()]
    if existing:
        print(f"[skip] extraction target {out_dir} already contains {len(existing)} files")
        return
    print(f"[unzip] {archive} -> {out_dir}")
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(out_dir)
    n = len([p for p in out_dir.rglob("*") if p.is_file()])
    print(f"[done] extracted {n} files")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the PLEIAData Zenodo archive.")
    parser.add_argument("--record-id", default=DEFAULT_RECORD_ID)
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--interim-dir", default="data/interim")
    parser.add_argument("--verify-md5", action="store_true",
                        help="Verify the archive MD5 against the Zenodo metadata (slower).")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    interim_dir = Path(args.interim_dir)

    meta = fetch_record_metadata(args.record_id)
    files = meta.get("files", [])
    if not files:
        raise SystemExit("No files listed on the Zenodo record; aborting.")

    for f in files:
        name = f["key"]
        url = f["links"]["self"]
        size = f.get("size")
        dest = raw_dir / name
        download_file(url, dest, expected_size=size)

        if args.verify_md5:
            checksum = f.get("checksum", "")
            if checksum.startswith("md5:"):
                actual = md5_of(dest)
                expected = checksum.split(":", 1)[1]
                status = "OK" if actual == expected else "MISMATCH"
                print(f"[md5 ] {name}: {status} ({actual})")
                if status == "MISMATCH":
                    raise SystemExit("MD5 verification failed.")

        if dest.suffix.lower() == ".zip":
            extract_zip(dest, interim_dir)


if __name__ == "__main__":
    main()
