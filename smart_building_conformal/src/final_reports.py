"""Compatibility entry point for evidence-gated reports."""
from pathlib import Path
from .final_reports_v2 import HONESTY, build as build_v2


def build(run_root, out_root, datasets):
    return build_v2(out_root, run_root, Path(out_root) / "runs" / "unavailable_extension", datasets)
