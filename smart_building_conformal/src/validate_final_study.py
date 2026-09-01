"""Machine-checkable gate for the corrected final dissertation study.

    python -m src.validate_final_study --output-root outputs/final_dissertation_v2

Exits non-zero unless every check passes; only then does it write
``PUBLICATION_READY.json``. The point is that a partial or leaky study can never
be labelled publication-ready by hand — the marker exists only as a by-product of
a clean validation, and it records the exact code/protocol/config/data lineage
that was checked.

Checks that do not depend on a completed run (protocol parses, hashes recorded,
``outputs/full_study`` unchanged, no audit item still ``PENDING``) are enforced
now. Run-dependent checks look for the completed run's artefacts and FAIL — rather
than silently pass — when they are absent, so running the validator today
correctly reports that the study is not yet publication-ready.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    def add(self, name, ok, detail=""):
        self.checks.append(Check(name, bool(ok), detail))
        return ok

    @property
    def passed(self) -> bool:
        return all(c.ok for c in self.checks)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _full_study_unchanged(rep: Report, out_root: Path) -> None:
    baseline = out_root / "audit" / "full_study_baseline_checksums.txt"
    fs = ROOT / "outputs" / "full_study"
    if not baseline.exists():
        rep.add("full_study_baseline_recorded", False,
                f"missing {baseline}")
        return
    want = {}
    for line in baseline.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, path = line.partition(" ")
        want[path.lstrip("*").strip()] = digest
    current = {}
    for p in sorted(fs.rglob("*")):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            current[rel] = _sha256_file(p)
    # Compare on the paths recorded in the baseline (relative form may differ by
    # a leading directory; match on suffix).
    mismatches = []
    for path, digest in want.items():
        base = path.split("outputs/full_study/", 1)[-1]
        hit = next((d for rp, d in current.items()
                    if rp.endswith("outputs/full_study/" + base)
                    or rp.endswith(base)), None)
        if hit is None:
            mismatches.append(f"missing {base}")
        elif hit != digest:
            mismatches.append(f"changed {base}")
    rep.add("full_study_unchanged", not mismatches,
            "ok" if not mismatches else "; ".join(mismatches[:5]))


def _protocol_ok(rep: Report, out_root: Path) -> None:
    proto = out_root / "protocol" / "frozen_protocol.yaml"
    hashfile = out_root / "protocol" / "config_hash.txt"
    try:
        from . import protocol as P
        p = P.load_protocol(proto)
        rep.add("protocol_parses_and_validates", True,
                f"schema_version={p.schema_version}")
        h = P.protocol_hash(proto)
        recorded = hashfile.read_text(encoding="utf-8") if hashfile.exists() else ""
        rep.add("protocol_hash_recorded", h in recorded,
                f"canonical={h[:16]}...")
    except Exception as exc:                                # noqa: BLE001
        rep.add("protocol_parses_and_validates", False, f"{type(exc).__name__}: {exc}")


def _no_pending_audit(rep: Report, out_root: Path) -> None:
    audit = out_root / "audit" / "leakage_audit.json"
    if not audit.exists():
        rep.add("no_audit_item_pending", False, f"missing {audit}")
        return
    data = json.loads(audit.read_text(encoding="utf-8"))
    pending = [f["id"] for f in data.get("findings", [])
               if f.get("status") == "PENDING"]
    rep.add("no_audit_item_pending", not pending,
            "none pending" if not pending else f"PENDING: {', '.join(pending)}")


def _engine_smoke_covers_all(rep: Report, out_root: Path) -> None:
    """Readiness: a fast engine smoke covered all four datasets and four ablations."""
    summ = out_root / "runs" / "engine_smoke" / "engine_summary.json"
    if not summ.exists():
        rep.add("engine_smoke_all_datasets", False,
                "no runs/engine_smoke/engine_summary.json")
        rep.add("engine_smoke_four_ablations", False, "no engine smoke")
        return
    data = json.loads(summ.read_text(encoding="utf-8"))
    ds = data.get("datasets", {})
    want_ds = {"pleia", "pleia_energy", "rico", "bdg2"}
    have_ds = set(ds)
    rep.add("engine_smoke_all_datasets", want_ds <= have_ds,
            f"covered {sorted(have_ds)}")
    all_abl = set()
    for v in ds.values():
        all_abl |= set(v.get("ablation_levels", []))
    want_abl = {"baseline", "conformal_only", "temporal", "full"}
    rep.add("engine_smoke_four_ablations", want_abl <= all_abl,
            f"ablations {sorted(all_abl)}")


def _completed_run(rep: Report, out_root: Path) -> None:
    runs = out_root / "runs"
    full = [p for p in sorted(runs.glob("full_*"))
            if (p / "engine_summary.json").exists()] if runs.exists() else []
    if not full:
        rep.add("full_nonfast_run_present", False,
                "no runs/full_* with engine_summary.json; full study not complete")
        for c in ("run_matrix_complete", "estimates_with_cis_present",
                  "reports_no_placeholders", "figures_trace_to_csv"):
            rep.add(c, False, "no completed run to validate")
        return
    run = full[-1]
    summ = json.loads((run / "engine_summary.json").read_text(encoding="utf-8"))
    fast = bool(summ.get("fast", True))
    rep.add("full_nonfast_run_present", not fast, f"run={run.name}, fast={fast}")

    want_ds = {"pleia", "pleia_energy", "rico", "bdg2"}
    ds = summ.get("datasets", {})
    complete = want_ds <= set(ds) and all(
        v.get("n_outer_rows", 0) > 0
        and {"baseline", "conformal_only", "temporal", "full"}
        <= set(v.get("ablation_levels", [])) for v in ds.values())
    rep.add("run_matrix_complete", complete,
            f"datasets {sorted(ds)}; folds "
            f"{sorted({v.get('n_folds') for v in ds.values()})}")

    cis = out_root / "metrics" / "final_cis.csv"
    ok_cis = False
    if cis.exists():
        import csv
        with open(cis, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        ok_cis = bool(rows) and all(
            r.get("estimate") not in (None, "") and r.get("ci_low") not in (None, "")
            and r.get("ci_high") not in (None, "") for r in rows)
    rep.add("estimates_with_cis_present", ok_cis,
            f"{cis.name} {'ok' if ok_cis else 'missing/incomplete'}")

    results = out_root / "report" / "FINAL_DISSERTATION_RESULTS.md"
    placeholders = ("TODO", "TBD", "XXX", "PLACEHOLDER", "FIXME", "{{", "___",
                    "<PLACEHOLDER", "lorem ipsum")
    ok_rep = False
    if results.exists():
        text = results.read_text(encoding="utf-8")
        ok_rep = ("holdout" in text and
                  not any(tok in text for tok in placeholders))
    rep.add("reports_no_placeholders", ok_rep,
            "results report clean" if ok_rep else "missing/placeholder in report")

    figidx = out_root / "figures" / "figure_index.csv"
    ok_fig = False
    if figidx.exists():
        import csv
        with open(figidx, encoding="utf-8") as f:
            frows = list(csv.DictReader(f))
        ok_fig = bool(frows) and all(r.get("source_sha256") for r in frows)
    rep.add("figures_trace_to_csv", ok_fig,
            f"{len(frows) if ok_fig else 0} figures traced" if ok_fig
            else "no figure_index or missing source hashes")


def _lineage(out_root: Path) -> dict:
    """Code / protocol / run / artefact lineage for the publication marker."""
    info: dict = {}
    try:
        info["code_sha"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True,
            text=True).stdout.strip()
    except Exception:                                       # noqa: BLE001
        info["code_sha"] = "unknown"
    try:
        from . import protocol as P
        info["protocol_hash"] = P.protocol_hash(
            out_root / "protocol" / "frozen_protocol.yaml")
    except Exception:                                       # noqa: BLE001
        info["protocol_hash"] = "unknown"
    runs = out_root / "runs"
    full = [p for p in sorted(runs.glob("full_*"))
            if (p / "engine_summary.json").exists()] if runs.exists() else []
    info["run_id"] = full[-1].name if full else None
    for rel in ("metrics/final_cis.csv", "figures/figure_index.csv",
                "report/FINAL_DISSERTATION_RESULTS.md"):
        p = out_root / rel
        if p.exists():
            info[f"sha256:{rel}"] = _sha256_file(p)
    return info


def run(output_root: str, *, run_tests: bool, mode: str = "publication") -> Report:
    out_root = (ROOT / output_root) if not Path(output_root).is_absolute() \
        else Path(output_root)
    rep = Report()
    _protocol_ok(rep, out_root)
    _full_study_unchanged(rep, out_root)
    _no_pending_audit(rep, out_root)
    if run_tests:
        try:
            r = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=",
                                "-q"], cwd=str(ROOT), capture_output=True,
                               text=True, timeout=1800)
            rep.add("tests_pass", r.returncode == 0,
                    (r.stdout.strip().splitlines() or ["?"])[-1])
        except Exception as exc:                            # noqa: BLE001
            rep.add("tests_pass", False, f"{type(exc).__name__}: {exc}")
    if mode == "readiness":
        # Ready for the full run: design clean + engine smoke covers everything.
        _engine_smoke_covers_all(rep, out_root)
    else:
        # Publication: requires the completed non-fast run, CIs, figures, reports.
        _completed_run(rep, out_root)
    return rep


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate the corrected final study.")
    ap.add_argument("--output-root", default="outputs/final_dissertation_v2")
    ap.add_argument("--run-tests", action="store_true",
                    help="also run the full pytest suite as a check")
    ap.add_argument("--mode", choices=["readiness", "publication"],
                    default="publication",
                    help="readiness: ready for the full run; publication: full run "
                         "complete with CIs/figures/reports")
    args = ap.parse_args()

    rep = run(args.output_root, run_tests=args.run_tests, mode=args.mode)
    print(f"{'CHECK':50s} RESULT")
    for c in rep.checks:
        print(f"{c.name:50s} {'PASS' if c.ok else 'FAIL':5s} {c.detail}")

    out_root = ROOT / args.output_root
    if rep.passed:
        if args.mode == "publication":
            marker = out_root / "PUBLICATION_READY.json"
            payload = {"publication_ready": True,
                       "checks": [c.name for c in rep.checks],
                       **_lineage(out_root),
                       "note": "written only because every publication check passed"}
            marker.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"\nALL PUBLICATION CHECKS PASSED -> wrote {marker}")
        else:
            print("\nREADINESS CHECKS PASSED -> repository is ready for the full run "
                  "(PUBLICATION_READY.json is written only after the full run).")
        sys.exit(0)
    else:
        n_fail = sum(1 for c in rep.checks if not c.ok)
        print(f"\n{n_fail} check(s) failed in {args.mode} mode.")
        sys.exit(1)


if __name__ == "__main__":
    main()
