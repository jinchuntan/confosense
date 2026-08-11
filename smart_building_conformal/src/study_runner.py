"""Dataset-agnostic orchestration of the full dissertation study.

One code path serves PLEIAData, RICO and BDG2. Everything dataset-specific has
already been resolved by the time execution reaches here: the adapter has lowered
its source into :class:`~src.datasets.base.PreparedDataset`, and partitioning,
seasonality support and group structure travel with that object. The stages below
therefore branch on *capabilities* ("does this dataset support a seasonal
baseline?") rather than on dataset names.

Stages, in order, each independently resumable:

``prepare``        adapter → prepared dataset, data profiles, split audits
``point``          persistence / seasonal naive / XGBoost / Attention-LSTM
``intervals``      quantile_uncalibrated / cqr / recentred EnbPI / dscp
``alerts``         calibration rule surface, frozen rule, test sensitivity
``recalibration``  static / periodic / rolling, with recovery profiles
``robustness``     disturbance scenarios, legacy-fixed and closed-loop
``statistics``     bootstrap CIs, Diebold-Mariano, effect sizes

Method naming is deliberate and is carried through to every output file:
``quantile_uncalibrated`` is never merged with ``cqr``; the adapted EnbPI is
always ``recentred_enbpi_static`` / ``recentred_enbpi_updated`` and never plain
"EnbPI"; ``dscp`` means the procedure in :mod:`src.conformal_dscp`.

Where a method genuinely cannot apply — the seasonal-naive baseline on RICO's
four-hour runs, for instance — the run records it as *not applicable*, with the
reason, and continues. Nothing is quietly substituted.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import alert_study, attention_lstm, conformal_cqr, conformal_dscp
from . import conformal_enbpi, conformal_quantile
from . import metrics as M
from . import recalibration as recal
from . import robustness_study as rob
from . import statistics as S
from . import windowing, xgboost_model
from .datasets import get_adapter
from .datasets.base import ChronologicalPartitioner
from .residuals import DelayedResidualPool

PARTITIONS = ("train", "calibration", "test")

INTERVAL_METHODS = ("quantile_uncalibrated", "cqr",
                    "recentred_enbpi_static", "recentred_enbpi_updated", "dscp")


def _sub(obj, mask):
    return windowing.subset(obj, mask)


def _where(exc: BaseException) -> str:
    """Innermost ``file:line`` of a caught exception.

    A stage failure is recorded as a limitation rather than crashing the study,
    so the location has to travel with the message; otherwise a failure that is
    reported honestly is still undebuggable.
    """
    import traceback
    frames = traceback.extract_tb(exc.__traceback__)
    if not frames:
        return "unknown location"
    last = frames[-1]
    return f"{Path(last.filename).name}:{last.lineno} in {last.name}"


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


class DatasetStudy:
    """Runs every stage for one dataset and persists its outputs."""

    def __init__(self, dataset_id: str, cfg: dict, out_root: Path,
                 manifest, ledger, *, fast: bool = False,
                 only_stages: list[str] | None = None):
        self.dataset_id = dataset_id
        self.cfg = cfg
        self.out = out_root / dataset_id
        self.manifest = manifest
        self.ledger = ledger
        self.fast = fast
        self.only_stages = only_stages
        self.seed = int(cfg.get("seed", 42))
        self.levels = list(cfg.get("coverage_levels", [0.90, 0.95]))
        self.horizons = list(cfg["horizons"])
        self.prepared = None
        self.windows: dict[int, dict] = {}
        self.artifacts: dict = {}
        for sub in ("data_profiles", "metrics", "predictions", "figures",
                    "models", "report"):
            (self.out / sub).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def wants(self, stage: str) -> bool:
        return not self.only_stages or stage in self.only_stages

    def _stage(self, name: str, fn, *, resumable: bool = True):
        """Run one stage with timing, resume support and failure capture.

        ``resumable=False`` forces execution even when the ledger has the stage:
        used by :meth:`run`, which resumes whole datasets rather than individual
        stages because stages share in-memory artefacts.
        """
        key = f"{self.dataset_id}:{name}"
        if not self.wants(name):
            self.manifest.record(key, "skipped", reason="not selected by --stage")
            return None
        if resumable and self.ledger.done(key):
            self.manifest.record(key, "skipped", reason="already complete (--resume)")
            return None
        t0 = time.time()
        try:
            result = fn()
        except Exception as exc:                          # noqa: BLE001
            self.manifest.record(key, "failed", time.time() - t0,
                                 reason=f"{type(exc).__name__}: {exc} [{_where(exc)}]")
            self.manifest.note_limitation(
                f"{key} did not complete: {type(exc).__name__}: {exc} [{_where(exc)}]"
            )
            print(f"    [FAIL] {key}: {type(exc).__name__}: {exc}")
            return None
        self.manifest.record(key, "completed", time.time() - t0)
        self.ledger.mark(key)
        return result

    # ------------------------------------------------------------------ #
    # Stage: prepare
    # ------------------------------------------------------------------ #
    def stage_prepare(self):
        # A config block may point at a different adapter than its own key, which
        # is how PLEIAData exposes both a temperature and an energy target.
        adapter = get_adapter(self.cfg.get("adapter", self.dataset_id))
        prepared = adapter.prepare(self.cfg)
        self.prepared = prepared

        prof = self.out / "data_profiles"
        adapter.profile(prepared).to_csv(prof / "series_profile.csv", index=False)
        prepared.split_summary().to_csv(prof / "split_summary.csv", index=False)
        with open(prof / "partitioning.json", "w", encoding="utf-8") as f:
            json.dump(prepared.partitioner.describe(), f, indent=2, default=str)

        meta = prepared.metadata
        for key, name in [("selection_audit", "target_selection.csv"),
                          ("run_audit", "run_audit.csv"),
                          ("sensor_audit", "sensor_audit.csv"),
                          ("subset_selection", "subset_selection.csv")]:
            if isinstance(meta.get(key), pd.DataFrame):
                meta[key].to_csv(prof / name, index=False)

        prov = prepared.provenance.to_dict()
        prov["target_description"] = prepared.target_description
        for extra in ("target_rationale", "target_column"):
            if extra in meta:
                prov[extra] = meta[extra]
        self.manifest.add_provenance(self.dataset_id, prov)

        if not prepared.seasonal_naive_supported:
            self.manifest.note_limitation(
                f"{self.dataset_id}: seasonal-naive baseline is not applicable — "
                "no series carries a full seasonal cycle (reported as n/a, not "
                "approximated with a cross-group lag)."
            )

        # Build the supervised windows once and reuse them across stages.
        fcfg = windowing.feature_config(self.cfg, prepared.series[0].covariates)
        summaries = []
        for h in self.horizons:
            w = windowing.build_dataset_windows(prepared, h, fcfg)
            self.windows[h] = w
            summaries.append(windowing.window_summary(w))
            if w["skipped_groups"]:
                self.manifest.note_limitation(
                    f"{self.dataset_id} h={h}: {len(w['skipped_groups'])} group(s) "
                    "produced no complete window and were excluded at this horizon."
                )
        pd.concat(summaries, ignore_index=True).to_csv(
            prof / "window_summary.csv", index=False)
        return prepared

    # ------------------------------------------------------------------ #
    # Stage: point forecasting
    # ------------------------------------------------------------------ #
    def _point_for_horizon(self, h: int) -> dict:
        w = self.windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        tr, te = idx["train"], idx["test"]
        if tr.sum() == 0 or te.sum() == 0:
            raise ValueError(f"empty train ({tr.sum()}) or test ({te.sum()}) partition")

        X_train, y_train = _sub(X, tr), y[tr]
        X_test, y_test = _sub(X, te), y[te]

        preds: dict[str, np.ndarray] = {
            "persistence": meta.loc[te, "persistence_pred"].to_numpy(),
        }
        seed_preds: dict[str, dict] = {}
        notes: dict[str, str] = {}

        if self.prepared.seasonal_naive_supported:
            preds["seasonal_naive"] = meta.loc[te, "seasonal_naive_pred"].to_numpy()
        else:
            notes["seasonal_naive"] = (
                "not applicable: no series contains a full seasonal cycle"
            )

        # ---- XGBoost: tune once on training data, refit across seeds ----
        xcfg = self.cfg["models"]["xgboost"]
        tuned = xgboost_model.tune(
            X_train, pd.Series(y_train), n_iter=xcfg["search_iter"],
            n_splits=xcfg["cv_splits"], seed=self.seed,
            n_jobs=int(xcfg.get("search_n_jobs", -1)),
        )
        # XGBoost's `hist` tree method reduces gradient histograms in
        # thread-completion order, so its fitted model depends on how many
        # threads it was given: on this data the same seed yields MAE 0.3428 at
        # one thread and 0.3560 at four. The full study therefore refits
        # single-threaded, which costs about 1.6x on this stage and makes the
        # result independent of core count and machine load. Tuning is left
        # parallel because each candidate fit inside the search is already
        # single-threaded, and was verified bit-identical across runs.
        refit_n_jobs = int(xcfg.get("refit_n_jobs", -1))
        xgb_seeds = {}
        for s in range(self.seed, self.seed + int(xcfg["seeds"])):
            model = xgboost_model.fit_with_params(
                X_train, pd.Series(y_train), tuned["best_params"], s,
                n_jobs=refit_n_jobs)
            xgb_seeds[s] = xgboost_model.predict(model, X_test)
        preds["xgboost"] = xgb_seeds[self.seed]
        seed_preds["xgboost"] = xgb_seeds
        with open(self.out / "models" / f"xgboost_best_params_h{h}.json", "w") as f:
            json.dump({
                "best_params": tuned["best_params"],
                "best_cv_mae": tuned["best_cv_mae"],
                "refit_n_jobs": refit_n_jobs,
                "search_n_jobs": int(xcfg.get("search_n_jobs", -1)),
                "seeds": sorted(xgb_seeds),
                "xgboost_version": __import__("xgboost").__version__,
                "tree_method": "hist",
                "determinism_note": (
                    "refit_n_jobs=1 makes the fit independent of thread count; "
                    "any other value reintroduces thread-order nondeterminism"),
            }, f, indent=2)

        # ---- Attention-LSTM ----
        lcfg = self.cfg["models"]["lstm"]
        Xseq, have, _ = windowing.build_dataset_sequences(
            self.prepared, h, lcfg["seq_len"], meta)
        lstm_preds = np.full(len(y_test), np.nan)
        lstm_seeds: dict[int, np.ndarray] = {}
        tr_seq = tr & have
        te_seq = te & have
        if tr_seq.sum() >= 50 and te_seq.sum() > 0:
            te_pos = np.flatnonzero(te)
            fill = np.isin(te_pos, np.flatnonzero(te_seq))
            for s in range(self.seed, self.seed + int(lcfg["seeds"])):
                res = attention_lstm.train_predict(
                    Xseq[tr_seq], y[tr_seq], Xseq[te_seq], lcfg, s)
                full = np.full(len(y_test), np.nan)
                full[fill] = res["predictions"]
                lstm_seeds[s] = full
                if s == self.seed:
                    with open(self.out / "models" /
                              f"lstm_history_h{h}_seed{s}.json", "w") as f:
                        json.dump(res["history"], f, indent=2)
            lstm_preds = lstm_seeds[self.seed]
            preds["attention_lstm"] = lstm_preds
            seed_preds["attention_lstm"] = lstm_seeds
        else:
            notes["attention_lstm"] = (
                f"not run: only {int(tr_seq.sum())} training and {int(te_seq.sum())} "
                "test sequences survived the sequence-length requirement"
            )
            self.manifest.note_limitation(
                f"{self.dataset_id} h={h}: Attention-LSTM not run "
                f"({notes['attention_lstm']})."
            )

        # ---- metrics ----
        base_mae, base_rmse = M.mae(y_test, preds["persistence"]), M.rmse(y_test, preds["persistence"])
        rows = []
        for name in ["persistence", "seasonal_naive", "xgboost", "attention_lstm"]:
            if name not in preds:
                rows.append({**self._ctx(h), "point_model": name,
                             "applicable": False, "note": notes.get(name, ""),
                             "n_seeds": 0})
                continue
            p = preds[name]
            sp = seed_preds.get(name)
            mae, rmse = M.mae(y_test, p), M.rmse(y_test, p)
            row = {
                **self._ctx(h), "point_model": name, "applicable": True, "note": "",
                "mae": mae, "rmse": rmse,
                "pct_mae_improvement": M.pct_improvement(base_mae, mae),
                "pct_rmse_improvement": M.pct_improvement(base_rmse, rmse),
                "n_seeds": len(sp) if sp else 1,
                "n_test": M.n_valid(y_test, p),
            }
            if sp:
                maes = [M.mae(y_test, v) for v in sp.values()]
                rmses = [M.rmse(y_test, v) for v in sp.values()]
                row["mae_std"] = float(np.std(maes))
                row["rmse_std"] = float(np.std(rmses))
                row["seeds_used"] = ",".join(str(k) for k in sp)
            rows.append(row)

        pred_df = pd.DataFrame({
            "dataset": self.dataset_id, "horizon": h,
            "group_id": meta.loc[te, "group_id"].to_numpy(),
            "target_time": meta.loc[te, "target_time"].to_numpy(),
            "y_true": y_test,
            **{k: v for k, v in preds.items()},
        })
        return {"rows": rows, "preds": preds, "pred_df": pred_df,
                "y_test": y_test, "seed_preds": seed_preds, "notes": notes}

    def stage_point(self):
        all_rows, frames = [], []
        self.artifacts["point"] = {}
        for h in self.horizons:
            res = self._point_for_horizon(h)
            all_rows.extend(res["rows"])
            frames.append(res["pred_df"])
            self.artifacts["point"][h] = res
        _write(pd.DataFrame(all_rows), self.out / "metrics" / "point_metrics.csv")
        pd.concat(frames, ignore_index=True).to_csv(
            self.out / "predictions" / "point_predictions.csv", index=False)
        return all_rows

    # ------------------------------------------------------------------ #
    def _ctx(self, h: int, **extra) -> dict:
        freq = self.prepared.freq
        return {
            "dataset": self.dataset_id,
            "target": self.prepared.series[0].target_id,
            "target_kind": self.prepared.metadata.get("target_kind", ""),
            "units": self.prepared.series[0].units,
            "sampling_freq": str(freq),
            "horizon_steps": h,
            "horizon_minutes": self.prepared.horizon_minutes(h),
            **extra,
        }

    # ------------------------------------------------------------------ #
    # Stage: intervals
    # ------------------------------------------------------------------ #
    def stage_intervals(self):
        rows, pred_frames = [], []
        self.artifacts["intervals"] = {}
        dscp_store: dict[float, dict] = {}

        for h in self.horizons:
            w = self.windows[h]
            idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
            tr, ca, te = idx["train"], idx["calibration"], idx["test"]
            X_tr, y_tr = _sub(X, tr), pd.Series(y[tr])
            X_ca, y_ca = _sub(X, ca), pd.Series(y[ca])
            X_te, y_te = _sub(X, te), y[te]
            tt = meta.loc[te, "target_time"].to_numpy()
            gid = meta.loc[te, "group_id"].to_numpy()
            store: dict = {}

            for level in self.levels:
                # ---- CQR and its uncalibrated counterpart ----
                cqr_seeds = []
                model = None
                for s in range(self.seed, self.seed + int(self.cfg["conformal"]["cqr"]["seeds"])):
                    mdl = conformal_cqr.fit_cqr(X_tr, y_tr, X_ca, y_ca, level, s)
                    cqr_seeds.append(conformal_cqr.cqr_interval(mdl, X_te))
                    if s == self.seed:
                        model = mdl
                primary = cqr_seeds[0]
                store[("cqr", level)] = {"model": model, **primary}
                rows.append(self._interval_row("cqr", h, level, y_te, primary,
                                               cqr_seeds, "HistGBR-quantile"))
                pred_frames.append(self._interval_frame("cqr", h, level, tt, gid, y_te, primary))

                try:
                    unc = conformal_quantile.quantile_interval(model, X_te)
                    store[("quantile_uncalibrated", level)] = unc
                    rows.append(self._interval_row(
                        conformal_quantile.METHOD_NAME, h, level, y_te, unc, None,
                        "HistGBR-quantile"))
                    pred_frames.append(self._interval_frame(
                        conformal_quantile.METHOD_NAME, h, level, tt, gid, y_te, unc))
                except RuntimeError as exc:
                    self.manifest.note_limitation(
                        f"{self.dataset_id} h={h}: uncalibrated quantile baseline "
                        f"unavailable ({exc})")

            # ---- recentred EnbPI ----
            try:
                enb_seeds = [
                    conformal_enbpi.run_enbpi(
                        X_tr, y_tr, X_ca, y_ca, X_te, pd.Series(y_te),
                        self.levels, self.cfg["conformal"]["enbpi"], s)
                    for s in range(self.seed,
                                   self.seed + int(self.cfg["conformal"]["enbpi"]["seeds"]))
                ]
                base_name = enb_seeds[0]["base_estimator"]
                for variant in ("static", "updated"):
                    name = f"recentred_enbpi_{variant}"
                    for level in self.levels:
                        primary = enb_seeds[0][variant][level]
                        seeds = [r[variant][level] for r in enb_seeds]
                        store[(name, level)] = primary
                        rows.append(self._interval_row(name, h, level, y_te,
                                                       primary, seeds, base_name))
                        pred_frames.append(self._interval_frame(
                            name, h, level, tt, gid, y_te, primary))
            except Exception as exc:                       # noqa: BLE001
                self.manifest.note_limitation(
                    f"{self.dataset_id} h={h}: recentred EnbPI failed "
                    f"({type(exc).__name__}: {exc})")

            self.artifacts["intervals"][h] = store
            dscp_store[h] = {"X_ca": X_ca, "y_ca": y_ca, "X_te": X_te,
                             "y_te": y_te, "tt": tt, "gid": gid, "meta": meta,
                             "idx": idx}

        # ---- DSCP: needs the multi-step vector across horizons ----
        try:
            rows_d, frames_d = self._run_dscp(dscp_store)
            rows.extend(rows_d)
            pred_frames.extend(frames_d)
        except Exception as exc:                            # noqa: BLE001
            self.manifest.note_limitation(
                f"{self.dataset_id}: DSCP did not run ({type(exc).__name__}: {exc})")

        _write(pd.DataFrame(rows), self.out / "metrics" / "interval_metrics.csv")
        if pred_frames:
            pd.concat(pred_frames, ignore_index=True).to_csv(
                self.out / "predictions" / "interval_predictions.csv", index=False)
        return rows

    def _interval_row(self, method, h, level, y_true, res, seeds, point_model):
        im = M.interval_metrics(y_true, res["lower"], res["upper"], level)
        scale = float(np.nanstd(y_true)) or float("nan")
        row = {
            **self._ctx(h), "point_model": point_model, "conformal_method": method,
            "nominal_coverage": level, **im,
            "normalized_mean_interval_width": im["mean_interval_width"] / scale
            if np.isfinite(scale) and scale else float("nan"),
            "n_seeds": len(seeds) if seeds else 1,
            # Quantile crossings repaired by ordering the bounds, so the count
            # appears in the tables rather than being silently absorbed.
            "n_crossed_repaired": int(res.get("n_crossed_repaired", 0)),
        }
        if seeds:
            covs = [M.empirical_coverage(y_true, r["lower"], r["upper"]) for r in seeds]
            wids = [M.mean_interval_width(r["lower"], r["upper"]) for r in seeds]
            row["coverage_std"] = float(np.std(covs))
            row["width_std"] = float(np.std(wids))
        return row

    def _interval_frame(self, method, h, level, tt, gid, y_true, res):
        return pd.DataFrame({
            "dataset": self.dataset_id, "horizon": h, "conformal_method": method,
            "nominal_coverage": level, "group_id": gid, "target_time": tt,
            "y_true": y_true, "point": res["point"],
            "lower": res["lower"], "upper": res["upper"],
        })

    def _run_dscp(self, store: dict):
        """Fit DSCP on the per-origin multi-horizon prediction vector.

        The paper assumes one model emitting b steps at once; ConfoSense trains a
        separate direct model per horizon, so the sequence is assembled across
        horizon models that share a forecast origin. That deviation is documented
        in :mod:`src.conformal_dscp` and recorded as a limitation here.
        """
        dcfg = self.cfg.get("conformal", {}).get("dscp", {})
        horizons = [h for h in self.horizons if h in store]
        if len(horizons) < 2:
            raise ValueError("DSCP needs at least two horizons to form a step vector")

        self.manifest.note_limitation(
            "DSCP is applied to a multi-step vector assembled across ConfoSense's "
            "direct per-horizon models rather than a single multi-output model as "
            "in Yu et al. (2025); documented deviation."
        )

        # Align origins that exist at every horizon — separately per partition.
        # Intersecting across partitions as well would always be empty, since a
        # calibration origin is by construction never a test origin.
        keys: dict[str, set] = {}
        for part in ("calibration", "test"):
            for h in horizons:
                meta, idx = store[h]["meta"], store[h]["idx"]
                k = set(zip(meta.loc[idx[part], "group_id"],
                            meta.loc[idx[part], "origin_time"]))
                keys[part] = k if part not in keys else keys[part] & k
            if not keys[part]:
                raise ValueError(
                    f"no {part} forecast origin is present at every horizon "
                    f"{horizons}; DSCP needs a shared multi-step vector")

        def gather(part: str):
            frames = []
            for h in horizons:
                meta, idx = store[h]["meta"], store[h]["idx"]
                sub = meta.loc[idx[part], ["group_id", "origin_time", "y_true"]].copy()
                res = self.artifacts["intervals"][h][("cqr", self.levels[-1])]
                # The CQR median is the point forecast DSCP calibrates around.
                pt = res["point"] if part == "test" else None
                if part == "calibration":
                    model = self.artifacts["intervals"][h][("cqr", self.levels[-1])]["model"]
                    pt = conformal_cqr.cqr_interval(model, store[h]["X_ca"])["point"]
                sub["pred"] = pt
                allowed = keys[part]
                sub = sub[[tuple(x) in allowed for x in
                           zip(sub["group_id"], sub["origin_time"])]]
                sub = sub.sort_values(["group_id", "origin_time"]).reset_index(drop=True)
                frames.append(sub)
            base = frames[0][["group_id", "origin_time"]].copy()
            P = np.column_stack([f["pred"].to_numpy() for f in frames])
            Y = np.column_stack([f["y_true"].to_numpy() for f in frames])
            return base, P, Y

        _, P_ca, Y_ca = gather("calibration")
        base_te, P_te, Y_te = gather("test")

        rows, frames = [], []
        assignments = None
        for level in self.levels:
            cal = conformal_dscp.fit_dscp(
                P_ca, Y_ca, horizons,
                max_clusters=int(dcfg.get("max_clusters", 6)),
                ks_threshold=float(dcfg.get("ks_threshold", 0.05)),
                # None -> the paper's rule (size of the smallest cluster).
                neighbours=(int(dcfg["neighbours"])
                            if dcfg.get("neighbours") is not None else None),
                gamma=float(dcfg.get("gamma", 1.0)),
                seed=self.seed,
            )
            # The clustering is refit per level (its inputs do not depend on the
            # level, so it is identical each time) but the soft-DTW assignment
            # is the expensive part, so it is computed once and reused.
            if assignments is None:
                assignments = cal.assign(P_te)
            out = cal.predict_interval(P_te, level, assignments=assignments)
            for j, h in enumerate(horizons):
                res = {"point": out["point"][:, j], "lower": out["lower"][:, j],
                       "upper": out["upper"][:, j]}
                rows.append({**self._interval_row("dscp", h, level, Y_te[:, j], res,
                                                  None, "HistGBR-quantile"),
                             "dscp_n_clusters": cal.n_clusters,
                             "dscp_silhouette": cal.silhouette})
                # Each horizon of the shared step vector lands at its own target
                # time, so it is derived from the common origin rather than
                # reusing the origin itself.
                target_times = (pd.DatetimeIndex(base_te["origin_time"])
                                + h * self.prepared.freq)
                frames.append(self._interval_frame(
                    "dscp", h, level, target_times.to_numpy(),
                    base_te["group_id"].to_numpy(), Y_te[:, j], res))
            with open(self.out / "models" / f"dscp_level{int(level*100)}.json", "w") as f:
                json.dump({"n_clusters": cal.n_clusters, "silhouette": cal.silhouette,
                           "horizons": horizons, "merge_map": {str(k): v for k, v
                                                               in cal.merge_map.items()},
                           **cal.metadata}, f, indent=2, default=str)
        return rows, frames

    # ------------------------------------------------------------------ #
    # Stage: alerts
    # ------------------------------------------------------------------ #
    def stage_alerts(self):
        acfg = self.cfg["alerts"]
        h = int(acfg.get("primary_horizon", self.horizons[0]))
        level = float(acfg.get("primary_level", self.levels[-1]))
        method = acfg.get("primary_method", "cqr")
        if h not in self.artifacts.get("intervals", {}):
            raise ValueError(f"no intervals available at the operating horizon {h}")
        key = (method, level)
        if key not in self.artifacts["intervals"][h]:
            raise ValueError(f"interval method {method!r} at level {level} not available")
        if "model" not in self.artifacts["intervals"][h][key]:
            raise ValueError(
                f"alert rule selection needs a refittable interval model, but "
                f"{method!r} does not retain one; configure alerts.primary_method "
                "as 'cqr'"
            )
        w = self.windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        tr, ca, te = idx["train"], idx["calibration"], idx["test"]
        ti = self.artifacts["intervals"][h][key]

        y_ca, y_te = y[ca], y[te]
        o_ca = pd.DatetimeIndex(meta.loc[ca, "origin_time"])
        t_ca = pd.DatetimeIndex(meta.loc[ca, "target_time"])
        t_te = pd.DatetimeIndex(meta.loc[te, "target_time"])
        g_te = meta.loc[te, "group_id"].to_numpy()
        g_ca = meta.loc[ca, "group_id"].to_numpy()

        scale = self._train_scale(h)
        rules = alert_study.parse_rules(acfg.get("candidate_rules"))
        tol = int(acfg.get("detection_tolerance_steps", 6))
        freq = self.prepared.freq
        budget = float(acfg.get("max_false_alerts_per_day", 1.0))
        ctx = self._ctx(h, conformal_method=method, nominal_coverage=level)

        # ---- nested split: conformalize early, tune the rule late ----
        # Scoring rules on the observations that conformalized the interval model
        # makes the calibration violation rate optimistic — those residuals are
        # precisely the ones the conformal quantile was fitted to cover. So the
        # calibration period is cut chronologically: an earlier block
        # conformalizes a *separate* CQR model, and rules are scored on the later
        # block, which that model has never seen. The test partition is not
        # touched by any part of this.
        scfg = acfg.get("selection", {})
        split = alert_study.chronological_subsplit(
            o_ca, t_ca,
            fraction=float(scfg.get("calibration_conformal_fraction", 0.6)),
            min_samples=int(scfg.get("min_samples_per_block", 200)),
        )
        X_ca = _sub(X, ca)
        if split["usable"]:
            conf_m, rule_m = split["conformal_mask"], split["rule_mask"]
            sel_model = conformal_cqr.fit_cqr(
                _sub(X, tr), pd.Series(y[tr]),
                _sub(X_ca, conf_m), pd.Series(y_ca[conf_m]), level, self.seed)
            ci = conformal_cqr.cqr_interval(sel_model, _sub(X_ca, rule_m))
            y_sel, t_sel, g_sel = y_ca[rule_m], t_ca[rule_m], g_ca[rule_m]
            sel_partition = "calibration_rule_block"
        else:
            # Too few windows on one side to choose defensibly. Fall back to the
            # pooled construction rather than select on a handful of points, and
            # say so in the limitations instead of leaving it implicit.
            sel_model = self.artifacts["intervals"][h][key]["model"]
            ci = conformal_cqr.cqr_interval(sel_model, X_ca)
            y_sel, t_sel, g_sel = y_ca, t_ca, g_ca
            sel_partition = "calibration_pooled_fallback"
            self.manifest.note_limitation(
                f"{self.dataset_id}: {split['reason']}; the alert rule was scored "
                "on the full calibration partition, which also conformalized the "
                "interval model, so its calibration violation rate is optimistic."
            )

        # ---- rule-block surface -> frozen rule ----
        pert_ca, cat_ca = alert_study.inject_events(
            y_sel, scale, freq, t_sel, acfg["events"], seed=self.seed + 50,
            dataset=self.dataset_id, target=self.prepared.series[0].target_id,
            partition=sel_partition, group_ids=g_sel)
        surface_ca = alert_study.rule_surface(
            pert_ca, ci["lower"], ci["upper"], cat_ca, rules, freq, tol,
            context=ctx, role="calibration_selection")
        surface_ca["selection_partition"] = sel_partition
        surface_ca["n_selection_windows"] = len(y_sel)
        chosen, reason = alert_study.select_rule(surface_ca, budget)
        k, m = rules[chosen]

        split_row = {**ctx, **{key_: val for key_, val in split.items()
                               if not key_.endswith("_mask")},
                     "selection_partition": sel_partition,
                     "conformalized_on": ("calibration_early_block"
                                          if split["usable"] else "calibration_full"),
                     "test_first_target": t_te.min(), "test_last_target": t_te.max(),
                     "selected_rule": chosen}
        _write(pd.DataFrame([split_row]),
               self.out / "metrics" / "alert_selection_split.csv")

        # ---- test: clean, then injected; every rule scored post hoc ----
        pert_te, cat_te = alert_study.inject_events(
            y_te, scale, freq, t_te, acfg["events"], seed=self.seed + 100,
            dataset=self.dataset_id, target=self.prepared.series[0].target_id,
            partition="test", group_ids=g_te)
        surface_te = alert_study.rule_surface(
            pert_te, ti["lower"], ti["upper"], cat_te, rules, freq, tol,
            context=ctx, role="post_hoc_sensitivity")
        surface_clean = alert_study.rule_surface(
            y_te, ti["lower"], ti["upper"], cat_te.iloc[0:0], rules, freq, tol,
            context=ctx, role="clean_test_no_events")

        for df, sel in ((surface_ca, chosen), (surface_te, chosen), (surface_clean, chosen)):
            df["selected_operating_rule"] = df["rule"] == sel
            df["selection_reason"] = reason

        pd.concat([cat_ca, cat_te], ignore_index=True).to_csv(
            self.out / "data_profiles" / "injected_event_catalog.csv", index=False)
        _write(surface_ca, self.out / "metrics" / "alert_rule_selection_calibration.csv")
        _write(pd.concat([surface_te, surface_clean], ignore_index=True),
               self.out / "metrics" / "alert_rule_sensitivity_test.csv")
        _write(pd.concat([surface_ca, surface_te, surface_clean], ignore_index=True),
               self.out / "metrics" / "alert_metrics.csv")

        self.artifacts["alerts"] = {
            "rule": (k, m), "rule_name": chosen, "horizon": h, "level": level,
            "method": method, "scale": scale, "catalog_test": cat_te,
            "perturbed_test": pert_te, "split": split_row,
        }
        return surface_ca

    # ------------------------------------------------------------------ #
    def rehydrate_primary_intervals(self) -> dict:
        """Rebuild only the CQR artefacts the post-interval stages consume.

        ``alerts``, ``recalibration`` and ``robustness`` all read one object: the
        CQR model conformalized at the operating horizon and level, plus its test
        interval. Re-running the whole ``intervals`` stage to recover it costs
        hours — 2.6 of them on BDG2, almost entirely EnbPI's online updates — for
        a single :func:`fit_cqr` call.

        The refit is only trustworthy if it reproduces the fit the study actually
        reported, so the regenerated test bounds are checked against the persisted
        ``interval_predictions.csv`` and the largest discrepancy is returned. A
        mismatch beyond floating-point noise raises rather than letting a
        re-audited rule be scored against a model the outputs never saw.
        """
        acfg = self.cfg["alerts"]
        h = int(acfg.get("primary_horizon", self.horizons[0]))
        level = float(acfg.get("primary_level", self.levels[-1]))
        w = self.windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        tr, ca, te = idx["train"], idx["calibration"], idx["test"]

        model = conformal_cqr.fit_cqr(
            _sub(X, tr), pd.Series(y[tr]), _sub(X, ca), pd.Series(y[ca]),
            level, self.seed)
        res = conformal_cqr.cqr_interval(model, _sub(X, te))

        check = {"verified_against_persisted": False, "max_abs_diff": float("nan"),
                 "n_compared": 0}
        path = self.out / "predictions" / "interval_predictions.csv"
        if path.exists():
            saved = pd.read_csv(path)
            saved = saved[(saved["conformal_method"] == "cqr")
                          & (saved["horizon"] == h)
                          & (np.isclose(saved["nominal_coverage"], level))]
            if len(saved) == len(res["lower"]):
                diff = max(
                    float(np.nanmax(np.abs(saved["lower"].to_numpy() - res["lower"]))),
                    float(np.nanmax(np.abs(saved["upper"].to_numpy() - res["upper"]))),
                )
                check = {"verified_against_persisted": True, "max_abs_diff": diff,
                         "n_compared": len(saved)}
                if diff > 1e-8:
                    raise ValueError(
                        f"{self.dataset_id}: refitted CQR at h={h} level={level} "
                        f"differs from the persisted interval predictions by "
                        f"{diff:.3e}; the reported outputs were produced by a "
                        "different fit, so reusing this model would be dishonest"
                    )
            else:
                check["reason"] = (f"row count {len(saved)} != {len(res['lower'])}; "
                                   "skipped the exactness check")
        else:
            check["reason"] = "no persisted interval predictions to check against"

        self.artifacts.setdefault("intervals", {}).setdefault(h, {})[("cqr", level)] = {
            "model": model, **res}
        self.artifacts["rehydration"] = {"horizon": h, "level": level, **check}
        return self.artifacts["rehydration"]

    def _train_scale(self, h: int) -> float:
        """Target dispersion from the **training** partition only."""
        w = self.windows[h]
        vals = w["y"][w["idx"]["train"]]
        s = float(np.nanstd(vals))
        return s if np.isfinite(s) and s > 0 else 1.0

    # ------------------------------------------------------------------ #
    # Stage: recalibration
    # ------------------------------------------------------------------ #
    def stage_recalibration(self):
        rcfg = self.cfg.get("recalibration", {})
        h = int(self.cfg["alerts"].get("primary_horizon", self.horizons[0]))
        level = float(self.cfg["alerts"].get("primary_level", self.levels[-1]))
        w = self.windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        ca, te = idx["calibration"], idx["test"]
        model = self.artifacts["intervals"][h][("cqr", level)]["model"]

        ci = conformal_cqr.cqr_interval(model, _sub(X, ca))
        ti = self.artifacts["intervals"][h][("cqr", level)]
        y_ca, y_te = y[ca], y[te]

        # A dataset split chronologically *inside* each group (BDG2) has
        # calibration and test periods that interleave once the groups are
        # concatenated: building 3's calibration overlaps building 1's test in
        # wall-clock time. Pooling their residuals would let one building's
        # not-yet-observed truth widen another building's interval, so those
        # datasets are recalibrated one group at a time. A group-partitioned
        # dataset (RICO) needs no such treatment — every calibration run
        # precedes every test run — and is pooled as usual.
        per_group = (isinstance(self.prepared.partitioner, ChronologicalPartitioner)
                     and self.prepared.is_grouped)
        g_ca = meta.loc[ca, "group_id"].to_numpy()
        g_te = meta.loc[te, "group_id"].to_numpy()

        # Settings are shared across groups, so they are chosen on one group's
        # calibration replay: the concatenated calibration index is not
        # monotonic for a per-group split, and a replay needs a single ordered
        # timeline. The largest group is used, deterministically.
        o_ca_all = pd.DatetimeIndex(meta.loc[ca, "origin_time"])
        t_ca_all = pd.DatetimeIndex(meta.loc[ca, "target_time"])
        if per_group:
            counts = pd.Series(g_ca).value_counts()
            chosen_group = sorted(counts[counts == counts.max()].index)[0]
            sel = np.flatnonzero(g_ca == chosen_group)
            sel_point, sel_truth = ci["point"][sel], y_ca[sel]
            sel_o, sel_t = o_ca_all[sel], t_ca_all[sel]
        else:
            chosen_group = None
            sel_point, sel_truth, sel_o, sel_t = ci["point"], y_ca, o_ca_all, t_ca_all

        settings = recal.select_settings(
            sel_point, sel_truth, sel_o, sel_t, level, h, rcfg.get("grid", {}),
        )
        settings["settings_selected_on_group"] = chosen_group
        table = settings.pop("table", None)
        if isinstance(table, pd.DataFrame):
            _write(table, self.out / "metrics" / "recalibration_selection.csv")
        resid_ca, resid_te = y_ca - ci["point"], y_te - ti["point"]
        t_ca = pd.DatetimeIndex(meta.loc[ca, "target_time"])
        o_te = pd.DatetimeIndex(meta.loc[te, "origin_time"])
        t_te = pd.DatetimeIndex(meta.loc[te, "target_time"])

        def build_pools():
            """Yield (slot, pool) pairs covering every test row exactly once."""
            if not per_group:
                yield slice(None), DelayedResidualPool.build(
                    resid_ca, t_ca, resid_te, o_te, t_te, h)
                return
            for g in pd.unique(g_te):
                sel = np.flatnonzero(g_te == g)
                cal_sel = np.flatnonzero(g_ca == g)
                yield sel, DelayedResidualPool.build(
                    resid_ca[cal_sel], t_ca[cal_sel], resid_te[sel],
                    o_te[sel], t_te[sel], h)

        pools = list(build_pools())
        if per_group:
            self.manifest.note_limitation(
                f"{self.dataset_id}: recalibration is performed per group "
                f"({len(pools)} groups) because calibration and test periods "
                "interleave across groups once they are concatenated; pooling "
                "them would mix one group's unobserved truth into another's "
                "interval."
            )

        rows, recovery = [], []
        for strategy in recal.STRATEGIES:
            lower = np.empty(len(y_te)); upper = np.empty(len(y_te))
            n_updates = 0
            for slot, pool in pools:
                r = recal.apply_strategy(
                    ti["point"][slot], pool, level, strategy,
                    update_every=settings["update_every"],
                    window=settings["window"], min_samples=settings["min_samples"],
                )
                lower[slot], upper[slot] = r.lower, r.upper
                n_updates += r.n_updates
            res = recal.RecalibrationResult(
                lower, upper, ti["point"], n_updates,
                np.zeros(len(y_te), dtype=int), strategy, settings)
            im = M.interval_metrics(y_te, res.lower, res.upper, level)
            # The calibration replay chooses one (update_every, window) pair
            # across both adaptive strategies. When a *periodic* configuration
            # wins, `window` is None, and running "rolling" with an unbounded
            # window reproduces periodic exactly. Reporting those two rows as
            # independent strategies would claim a rolling-window result the
            # study never obtained, so the degeneracy is flagged in the data
            # rather than left for a reader to infer from a blank column.
            degenerate = (strategy == "rolling" and settings["window"] is None)
            rows.append({
                **self._ctx(h), "conformal_method": "cqr",
                "nominal_coverage": level, "recalibration_strategy": strategy,
                **im, "n_updates": res.n_updates,
                "update_every": settings["update_every"],
                "rolling_window": settings["window"],
                "min_samples": settings["min_samples"],
                "settings_source": settings["selection"],
                "residual_delay_steps": h,
                "strategy_is_distinct": not degenerate,
                "degeneracy_note": (
                    "the calibration replay selected an unwindowed configuration, "
                    "so rolling reduced to the same unbounded update procedure as "
                    "periodic; no distinct rolling-window result was identified"
                    if degenerate else ""
                ),
            })
            if degenerate:
                self.manifest.note_limitation(
                    f"{self.dataset_id}: rolling recalibration is not a distinct "
                    "result — the calibration replay selected an unwindowed "
                    "configuration, so the rolling row reproduces periodic "
                    "exactly. It must not be reported as a second strategy."
                )
            prof = recal.recovery_profile(
                y_te, res.lower, res.upper, level,
                shift_index=len(y_te) // 2,
                block=int(rcfg.get("recovery_block", 144)),
            )
            prof.insert(0, "recalibration_strategy", strategy)
            prof.insert(0, "dataset", self.dataset_id)
            recovery.append(prof)

        _write(pd.DataFrame(rows), self.out / "metrics" / "recalibration_metrics.csv")
        if recovery:
            _write(pd.concat(recovery, ignore_index=True),
                   self.out / "metrics" / "recalibration_recovery.csv")
        return rows

    # ------------------------------------------------------------------ #
    # Stage: robustness
    # ------------------------------------------------------------------ #
    def stage_robustness(self):
        cfgr = self.cfg.get("robustness", {})
        h = int(self.cfg["alerts"].get("primary_horizon", self.horizons[0]))
        level = float(self.cfg["alerts"].get("primary_level", self.levels[-1]))
        rule = self.artifacts.get("alerts", {}).get("rule", (3, 5))
        model = self.artifacts["intervals"][h][("cqr", level)]["model"]
        freq = self.prepared.freq
        scale = self._train_scale(h)
        fcfg = windowing.feature_config(self.cfg, self.prepared.series[0].covariates)
        scenarios = rob.default_scenarios(cfgr)
        modes = cfgr.get("modes", list(rob.MODES))

        w = self.windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        te = idx["test"]
        y_te = y[te]
        clean = self.artifacts["intervals"][h][("cqr", level)]

        rows = []
        for scenario in scenarios:
            for mode in modes:
                try:
                    rows.append(self._robustness_case(
                        scenario, mode, h, level, model, rule, freq, scale,
                        fcfg, clean, y_te, meta, te, cfgr))
                except Exception as exc:                   # noqa: BLE001
                    self.manifest.note_limitation(
                        f"{self.dataset_id} robustness {scenario.name}/{mode} "
                        f"failed: {type(exc).__name__}: {exc} [{_where(exc)}]")

        # Calibration contamination is a separate design: corrupt the calibration
        # partition, recalibrate, then evaluate on clean test data.
        for frac in rob.contamination_levels(cfgr):
            try:
                rows.append(self._contamination_case(frac, h, level, model, freq, scale))
            except Exception as exc:                       # noqa: BLE001
                self.manifest.note_limitation(
                    f"{self.dataset_id} calibration contamination {frac}: "
                    f"{type(exc).__name__}: {exc}")

        _write(pd.DataFrame(rows), self.out / "metrics" / "robustness_metrics.csv")
        return rows

    def _robustness_case(self, scenario, mode, h, level, model, rule, freq,
                         scale, fcfg, clean, y_te, meta, te, cfgr):
        ctx = {**self._ctx(h), "conformal_method": "cqr", "nominal_coverage": level,
               "mode": mode, **scenario.describe(),
               "alert_rule": f"{rule[0]}-of-{rule[1]}", "seed": self.seed}

        if scenario.kind == "none":
            res = rob.evaluate_intervals_and_alerts(
                y_te, y_te, clean["point"], clean["lower"], clean["upper"],
                level, rule, freq)
            return {**ctx, **res}

        if mode == "legacy_fixed_intervals":
            # Only the observation is perturbed; the clean intervals stay put.
            # The series carries its real timestamps so that the missingness
            # scenarios can re-impute with the pipeline's time-based rule.
            observed = rob.perturb_series(
                pd.Series(y_te, index=pd.DatetimeIndex(meta.loc[te, "target_time"])),
                np.ones(len(y_te), bool), scenario, scale, self.seed,
                block_steps=int(cfgr.get("block_steps", 12)),
                max_gap=self.cfg["missing"]["max_short_gap_steps"],
            ).to_numpy()
            res = rob.evaluate_intervals_and_alerts(
                y_te, observed, clean["point"], clean["lower"], clean["upper"],
                level, rule, freq)
            return {**ctx, **res}

        # ---- closed loop: perturb the observation series, rebuild features ----
        test_start = pd.DatetimeIndex(meta.loc[te, "origin_time"]).min()
        perturbed_series = []
        for s in self.prepared.series:
            frame = s.frame.copy(deep=True)
            # Comparing a DatetimeIndex already yields an ndarray, not an Index.
            region = np.asarray(frame.index >= test_start)
            if region.any():
                frame["target"] = rob.perturb_series(
                    frame["target"], region, scenario, scale, self.seed,
                    block_steps=int(cfgr.get("block_steps", 12)),
                    max_gap=self.cfg["missing"]["max_short_gap_steps"])
            perturbed_series.append(
                type(s)(dataset_id=s.dataset_id, target_id=s.target_id, frame=frame,
                        freq=s.freq, group_id=s.group_id, season_steps=s.season_steps,
                        covariates=s.covariates, units=s.units, metadata=s.metadata))

        prepared2 = type(self.prepared)(
            dataset_id=self.prepared.dataset_id, series=perturbed_series,
            partitioner=self.prepared.partitioner, provenance=self.prepared.provenance,
            target_description=self.prepared.target_description,
            metadata=self.prepared.metadata,
        )
        w2 = windowing.build_dataset_windows(prepared2, h, fcfg)
        te2 = w2["idx"]["test"]
        X2, meta2 = _sub(w2["X"], te2), w2["meta"].loc[te2].reset_index(drop=True)
        observed2 = w2["y"][te2]

        res2 = conformal_cqr.cqr_interval(model, X2)

        # Align the clean truth onto the perturbed rows so degradation is measured
        # against reality, not against the corrupted signal.
        truth = (meta.loc[te, ["group_id", "target_time", "y_true"]]
                 .rename(columns={"y_true": "y_clean"}))
        joined = meta2[["group_id", "target_time"]].merge(truth, how="left",
                                                          on=["group_id", "target_time"])
        y_clean = joined["y_clean"].to_numpy(dtype=float)

        out = rob.evaluate_intervals_and_alerts(
            y_clean, observed2, res2["point"], res2["lower"], res2["upper"],
            level, rule, freq)
        return {**ctx, **out, "n_rows_rebuilt": int(len(observed2))}

    def _contamination_case(self, frac, h, level, model, freq, scale):
        """Corrupt a fraction of calibration residuals, then judge on clean test."""
        w = self.windows[h]
        idx, X, y, meta = w["idx"], w["X"], w["y"], w["meta"]
        ca, te = idx["calibration"], idx["test"]
        ci = conformal_cqr.cqr_interval(model, _sub(X, ca))
        ti = self.artifacts["intervals"][h][("cqr", level)]
        y_ca, y_te = y[ca], y[te]

        rng = np.random.default_rng(self.seed + 900)
        y_ca_bad = np.array(y_ca, dtype=float, copy=True)
        n_bad = int(round(frac * len(y_ca_bad)))
        if n_bad:
            pos = rng.choice(len(y_ca_bad), size=n_bad, replace=False)
            y_ca_bad[pos] += rng.choice([-1.0, 1.0], size=n_bad) * 3.0 * scale

        resid = y_ca_bad - ci["point"]
        alpha = 1.0 - level
        lo_q, hi_q = np.quantile(resid, alpha / 2), np.quantile(resid, 1 - alpha / 2)
        lower, upper = ti["point"] + lo_q, ti["point"] + hi_q
        im = M.interval_metrics(y_te, lower, upper, level)
        return {
            **self._ctx(h), "conformal_method": "cqr", "nominal_coverage": level,
            "mode": "calibration_contamination", "scenario": f"calib_contam_{int(frac*100)}pct",
            "kind": "calibration_contamination", "severity": frac,
            "severity_label": f"{int(frac*100)}%", "seed": self.seed + 900,
            "n_contaminated": n_bad, **im,
        }

    # ------------------------------------------------------------------ #
    # Stage: statistics
    # ------------------------------------------------------------------ #
    def stage_statistics(self):
        n_boot = int(self.cfg.get("bootstrap", {}).get("n_boot", 1000))
        boot_rows, dm_tables, eff_rows = [], [], []
        pairs = [("xgboost", "persistence"), ("attention_lstm", "persistence"),
                 ("xgboost", "attention_lstm"), ("seasonal_naive", "persistence")]

        for h in self.horizons:
            art = self.artifacts.get("point", {}).get(h)
            if art is None:
                continue
            ctx = self._ctx(h)
            preds, y_te = art["preds"], art["y_test"]
            boot_rows.append(S.bootstrap_all_point_models(
                y_te, preds, context=ctx, n_boot=n_boot, seed=self.seed))
            dm = S.pairwise_dm_table(y_te, preds, pairs, horizon=h, context=ctx)
            if len(dm):
                dm_tables.append(dm)
            for a, b in pairs:
                if a in preds and b in preds:
                    eff_rows.append({**ctx, "model_a": a, "model_b": b,
                                     **S.effect_sizes(y_te, preds[a], preds[b],
                                                      n_boot=min(n_boot, 500),
                                                      seed=self.seed)})

        if boot_rows:
            _write(pd.concat(boot_rows, ignore_index=True),
                   self.out / "metrics" / "bootstrap_metrics.csv")
        if dm_tables:
            _write(pd.concat(dm_tables, ignore_index=True),
                   self.out / "metrics" / "diebold_mariano.csv")
        if eff_rows:
            _write(pd.DataFrame(eff_rows), self.out / "metrics" / "effect_sizes.csv")
        return boot_rows

    # ------------------------------------------------------------------ #
    STAGES = ("prepare", "point", "intervals", "alerts", "recalibration",
              "robustness", "statistics")

    def run(self) -> None:
        """Execute the dataset's stages, honouring resume at dataset granularity.

        Resume deliberately works per *dataset*, not per stage. The stages share
        in-memory state — ``intervals`` hands its fitted models to ``alerts``,
        ``recalibration`` and ``robustness`` — so skipping a middle stage while
        running a later one would fail on missing artefacts. A dataset whose
        every stage is already recorded is skipped whole; a partially complete
        one restarts from ``point``, which is correct rather than merely fast.

        ``prepare`` always runs regardless of the ledger: it is cheap, and it is
        what populates the prepared dataset the other stages read.
        """
        wanted = [s for s in self.STAGES if self.wants(s) and s != "prepare"]
        if wanted and all(self.ledger.done(f"{self.dataset_id}:{s}") for s in wanted):
            for s in wanted:
                self.manifest.record(f"{self.dataset_id}:{s}", "skipped",
                                     reason="dataset already complete (--resume)")
            print(f"  [{self.dataset_id}] already complete; skipped (--resume)")
            return

        print(f"  [{self.dataset_id}] prepare ...")
        self._stage("prepare", self.stage_prepare, resumable=False)
        if self.prepared is None:
            print(f"  [{self.dataset_id}] preparation unavailable; later stages skipped")
            return

        # A targeted re-run (``--stage alerts,robustness``) skips ``intervals``
        # but still needs its CQR artefact. Rebuild just that one model and
        # verify it against the persisted predictions, rather than spending hours
        # recomputing methods this invocation does not touch.
        needs_cqr = any(self.wants(s) for s in
                        ("alerts", "recalibration", "robustness"))
        if needs_cqr and not self.wants("intervals"):
            print(f"  [{self.dataset_id}] rehydrating primary CQR intervals ...")
            chk = self.rehydrate_primary_intervals()
            print(f"    verified against persisted predictions: "
                  f"{chk['verified_against_persisted']} "
                  f"(max |diff| = {chk['max_abs_diff']:.3e}, n = {chk['n_compared']})")

        for name, fn in [("point", self.stage_point),
                         ("intervals", self.stage_intervals),
                         ("alerts", self.stage_alerts),
                         ("recalibration", self.stage_recalibration),
                         ("robustness", self.stage_robustness),
                         ("statistics", self.stage_statistics)]:
            print(f"  [{self.dataset_id}] {name} ...")
            self._stage(name, fn, resumable=False)
