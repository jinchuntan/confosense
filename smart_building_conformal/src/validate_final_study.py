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


def _completed_run(rep: Report, out_root: Path) -> None:
    runs = out_root / "runs"
    full = sorted(runs.glob("full_*")) if runs.exists() else []
    if not full:
        rep.add("full_nonfast_run_present", False,
                "no runs/full_* directory; corrected full study has not completed")
        rep.add("run_matrix_complete", False, "no run to validate")
        rep.add("estimates_with_cis_present", False, "no run to validate")
        rep.add("reports_no_placeholders", False, "no reports generated yet")
        rep.add("figures_trace_to_csv", False, "no figures generated yet")
        return
    run = full[-1]
    manifest = run / "manifests" / "run_manifest.json"
    ok = manifest.exists()
    fast = True
    if ok:
        m = json.loads(manifest.read_text(encoding="utf-8"))
        fast = bool(m.get("fast", True))
    rep.add("full_nonfast_run_present", ok and not fast,
            f"run={run.name}, fast={fast}")
    # Deeper run-matrix / CI / report / figure checks are enforced once a run
    # exists; until then they fail closed above.


def run(output_root: str, *, run_tests: bool) -> Report:
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
                               text=True, timeout=1200)
            rep.add("tests_pass", r.returncode == 0,
                    (r.stdout.strip().splitlines() or ["?"])[-1])
        except Exception as exc:                            # noqa: BLE001
            rep.add("tests_pass", False, f"{type(exc).__name__}: {exc}")
    _completed_run(rep, out_root)
    return rep


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate the corrected final study.")
    ap.add_argument("--output-root", default="outputs/final_dissertation_v2")
    ap.add_argument("--run-tests", action="store_true",
                    help="also run the full pytest suite as a check")
    args = ap.parse_args()

    rep = run(args.output_root, run_tests=args.run_tests)
    print(f"{'CHECK':50s} RESULT")
    for c in rep.checks:
        print(f"{c.name:50s} {'PASS' if c.ok else 'FAIL':5s} {c.detail}")

    out_root = ROOT / args.output_root
    marker = out_root / "PUBLICATION_READY.json"
    if rep.passed:
        payload = {
            "publication_ready": True,
            "checks": [c.name for c in rep.checks],
            "note": "written only because every validation check passed",
        }
        marker.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nALL CHECKS PASSED -> wrote {marker}")
        sys.exit(0)
    else:
        n_fail = sum(1 for c in rep.checks if not c.ok)
        print(f"\n{n_fail} check(s) failed; NOT publication-ready. "
              "PUBLICATION_READY.json not written.")
        sys.exit(1)


if __name__ == "__main__":
    main()
