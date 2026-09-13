"""Read local data and record actual engine split/scale membership; never fit."""
from __future__ import annotations
import argparse
import gc
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src import corrected_study as E, windowing, protocol
from src.datasets import get_adapter
from src.run_study import load_config, resolve_dataset_config
from src.split_integrity import boundary_record, membership_hash, refit_split, causal_prepared, tuning_splits


def audit(config, out, phase):
    study = load_config(config)
    resolved = protocol.compile_to_config(protocol.load_protocol(study["protocol_ref"]["path"]), study)
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    boundaries, membership, scales = [], [], []
    for ds in study["datasets"]:
        cfg = resolve_dataset_config(study, ds)
        cfg.setdefault("paths", {}).update({k: v for k, v in study.get("paths", {}).items() if k != "full_study_dir"})
        for key in ["bdg2", "rico"]:
            cfg.setdefault(key, {})["auto_download"] = False
        prepared = get_adapter(cfg.get("adapter", ds)).prepare(cfg)
        if phase == "after":
            prepared = causal_prepared(prepared, cfg.get("missing", {}).get("max_short_gap_steps", 3))
        scheme = "chronological" if type(prepared.partitioner).__name__ == "ChronologicalPartitioner" else "whole_run_group_blocked"
        for h in cfg["horizons"]:
            w = windowing.build_dataset_windows(prepared, h, windowing.feature_config(cfg, prepared.series[0].covariates))
            meta, y = w["meta"], w["y"]; meta.attrs["split_scheme"] = scheme
            folds = E.make_outer_folds(meta, scheme, resolved["protocol"]["outer_folds"], h, prepared.freq)
            for fi, fold in enumerate(folds):
                trc = np.concatenate([fold["train"], fold["calibration"]])
                inner = E.inner_split(meta, trc, scheme, h, prepared.freq)
                if phase == "before":
                    order = np.argsort(meta.iloc[trc].origin_time.to_numpy(), kind="stable")
                    cut = int(.75 * len(trc)); tr, ca = trc[order[:cut]], trc[order[cut:]]
                else:
                    tr, ca = refit_split(meta, trc, scheme)
                roles = {**inner, "refit_train": tr, "refit_calibration": ca, "outer_test": fold["test"]}
                tag = {"phase": phase, "dataset": ds, "horizon": h, "outer_fold": fi, "scheme": scheme}
                for left, right in [("inner_train", "inner_calib"), ("inner_calib", "inner_select"), ("inner_select", "outer_test"), ("refit_train", "refit_calibration"), ("refit_calibration", "outer_test")]:
                    boundaries.append({**tag, "boundary": left + "->" + right, **boundary_record(meta, roles[left], roles[right], scheme)})
                for role, idx in roles.items():
                    sub = meta.iloc[idx]
                    for g, group in sub.groupby("group_id", dropna=False, sort=False):
                        membership.append({**tag, "role": role, "group_id": str(g), "n": len(group), "origin_min": str(group.origin_time.min()), "origin_max": str(group.origin_time.max()), "target_min": str(group.target_time.min()), "target_max": str(group.target_time.max()), "membership_sha256": membership_hash(meta, group.index.to_numpy())})
                for stage, allowed in [("inner", inner["inner_train"]), ("outer", tr)]:
                    used = np.flatnonzero((meta.partition == "train").to_numpy()) if phase == "before" else allowed
                    forbidden = np.setdiff1d(used, allowed)
                    scales.append({**tag, "stage": stage, "n_scale_rows": len(used), "n_outside_permitted_train": len(forbidden), "n_outer_test_scale_rows": len(set(used) & set(fold["test"])), "scale_origin_max": str(meta.iloc[used].origin_time.max()), "scale_target_max": str(meta.iloc[used].target_time.max()), "scale_membership_sha256": membership_hash(meta, used)})
                if phase == "after":
                    train_meta = meta.iloc[inner["inner_train"]].reset_index(drop=True)
                    train_meta.attrs["split_scheme"] = scheme
                    for ci, (a, b) in enumerate(tuning_splits(train_meta, 2, scheme)):
                        boundaries.append({**tag, "boundary": f"tuning_{ci}", **boundary_record(train_meta, a, b, scheme)})
            print(f"{phase}: {ds} h={h}, {len(meta)} windows, {len(folds)} folds", flush=True)
            del w, meta, y
        del prepared
        gc.collect()
    pd.DataFrame(boundaries).to_csv(out / "boundaries.csv", index=False)
    pd.DataFrame(membership).to_csv(out / "membership.csv", index=False)
    pd.DataFrame(scales).to_csv(out / "event_scale_membership.csv", index=False)
    b = pd.DataFrame(boundaries); s = pd.DataFrame(scales)
    summary = {"phase": phase, "boundary_rows": len(b), "unsafe_boundaries": int(((b.target_overlap_count > 0) | (b.row_overlap_count > 0) | (b.run_intersections > 0)).sum()), "scale_rows": len(s), "scale_rows_outside_training": int((s.n_outside_permitted_train > 0).sum()), "models_fitted": 0}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--config", default="configs/study_final_dissertation_v2.yaml")
    p.add_argument("--out", required=True); p.add_argument("--phase", choices=["before", "after"], required=True)
    a = p.parse_args(); audit(a.config, a.out, a.phase)
