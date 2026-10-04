"""Persistent, resumable supervisor for the high-coverage extension queue.

Runs under the system Python (psutil); every scientific step is a separate
process of the pinned scientific interpreter.  The supervisor holds an exclusive
lock, writes a heartbeat, launches at most one task per unit and at most
``max_workers`` tasks at once, launches nothing while RAM, commit or disk
headroom is below the protocol floors, retries non-scientific failures at most
twice, and never retries a scientific validation failure.  The pilot unit runs
first; other units start only after the pilot gate passes.

    python hc_supervisor.py launch      # detached start (refuses a duplicate)
    python hc_supervisor.py status      # print the heartbeat
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
RUN_ROOT = Path(r"D:\ConfoSenseStorage\runs\op005_hicov_v1")
SCIENCE = RUN_ROOT / "science_root"
FROZEN = SCIENCE / "review/operational005_causal_replay_20260925"
OWNERS = RUN_ROOT / "owners"
UNITS = RUN_ROOT / "units"
ANALYSIS = RUN_ROOT / "analysis_v1"
QUARANTINE = RUN_ROOT / "quarantine"
ROOT = RUN_ROOT / "supervisor"
LOCK = ROOT / "supervisor.lock"
STATUS = ROOT / "status.json"
EVENTS = ROOT / "events.jsonl"
CONTROL = ROOT / "control.json"
ATTEMPTS = ROOT / "attempts"
SCIENTIFIC_PYTHON = Path(r"C:\cfs_venv\Scripts\python.exe")
FOLDS, SEEDS, BLOCKS = (0, 1, 2), (42, 43, 44, 45, 46), 33
PILOT = (0, 42)
MAX_ATTEMPTS = 3
SCIENTIFIC_FAILURE_EXIT = 3
TIMEOUT_SECONDS = {"owner_fit": 3 * 3600, "owner_validate": 3 * 3600, "owner_resume": 3600, "run": 3 * 3600,
                   "validate": 3 * 3600, "resume": 3600, "pilot_gate": 3600, "aggregate": 3 * 3600}
RAM_FLOOR_FIRST = int(1.5 * 2**30)
RAM_FLOOR_ADDITIONAL = 2 * 2**30
COMMIT_FLOOR = 3 * 2**30
DISK_FLOOR = 8 * 2**30
POLL_SECONDS = 10


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")
    for attempt in range(6):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            time.sleep(.2 * (attempt + 1))
    os.replace(temporary, path)


def event(name: str, **values) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"utc": utc(), "event": name, **values}, default=str, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def tree(path: Path) -> dict:
    return {p.relative_to(path).as_posix(): sha256(p) for p in sorted(path.rglob("*")) if p.is_file()}


def passed(path: Path) -> bool:
    try:
        return bool(read(path).get("passed"))
    except (OSError, ValueError):
        return False


def commit_available() -> int:
    class Status(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    status = Status()
    status.dwLength = ctypes.sizeof(Status)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return int(status.ullAvailPageFile)


def resources() -> dict:
    memory = psutil.virtual_memory()
    return {"available_ram_bytes": int(memory.available), "total_ram_bytes": int(memory.total),
            "commit_available_bytes": commit_available(), "free_disk_bytes": int(shutil.disk_usage(RUN_ROOT).free),
            "cpu_percent": psutil.cpu_percent(interval=None)}


def unit_name(fold: int, seed: int) -> str:
    return f"bdg2_f{fold}_s{seed}"


def lane(kind: str) -> str:
    return {"run": "run", "validate": "validate", "resume": "resume"}.get(kind, "exclusive")


class Task:
    def __init__(self, kind: str, fold: int | None = None, seed: int | None = None, block: int | None = None):
        self.kind, self.fold, self.seed, self.block = kind, fold, seed, block
        self.unit = unit_name(fold, seed) if fold is not None else None
        self.key = "_".join(str(x) for x in (kind, self.unit, None if block is None else f"b{block:03d}") if x)

    @property
    def stage(self) -> Path:
        return UNITS / self.unit / "blocks" / f"block_{self.block:03d}"

    def done(self) -> bool:
        if self.kind == "owner_fit":
            return (OWNERS / self.unit / "OWNER_MANIFEST.json").exists()
        if self.kind == "owner_validate":
            return passed(OWNERS / self.unit / "OWNER_VALIDATION.json")
        if self.kind == "owner_resume":
            return passed(OWNERS / self.unit / "RESUME.json")
        if self.kind == "run":
            return (self.stage / "COMPLETE.json").exists()
        if self.kind == "validate":
            base = UNITS / self.unit / "validation" / f"block_{self.block:03d}"
            return passed(base.with_suffix(".json")) and passed(base.with_name(base.name + ".extended.json"))
        if self.kind == "resume":
            return passed(UNITS / self.unit / "resume" / f"block_{self.block:03d}.json")
        if self.kind == "pilot_gate":
            return passed(RUN_ROOT / "PILOT_VALIDATION.json")
        if self.kind == "aggregate":
            return passed(ANALYSIS / "COMPLETION_VALIDATION.json")
        raise ValueError(self.kind)

    def argv(self, attempt: int) -> list[str]:
        python = [str(SCIENTIFIC_PYTHON), "-B"]
        unit = ["--fold", str(self.fold), "--model-seed", str(self.seed)] if self.fold is not None else []
        if self.kind == "owner_fit":
            return python + [str(HERE / "hc_owner.py"), "fit-unit", *unit] + (["--reconcile-partials"] if attempt > 1 else [])
        if self.kind == "owner_validate":
            return python + [str(HERE / "hc_validate.py"), "validate-owners", *unit]
        if self.kind == "owner_resume":
            return python + [str(HERE / "hc_owner.py"), "resume-unit", *unit]
        if self.kind in ("run", "resume"):
            return python + [str(HERE / "hc_adapter.py"), "run-block", *unit, "--block-index", str(self.block)]
        if self.kind == "validate":
            return python + [str(HERE / "hc_validate.py"), "validate-block", *unit, "--block-index", str(self.block)]
        if self.kind == "pilot_gate":
            return python + [str(HERE / "hc_pilot_gate.py"), "gate"]
        if self.kind == "aggregate":
            return python + [str(HERE / "hc_aggregate.py"), "run"]
        raise ValueError(self.kind)


def build_tasks() -> tuple[list[Task], dict[str, list[str]]]:
    units = [PILOT] + [(f, s) for f in FOLDS for s in SEEDS if (f, s) != PILOT]
    tasks, deps = [], {}
    gate = Task("pilot_gate")
    for fold, seed in units:
        fit, validate, resume = (Task(k, fold, seed) for k in ("owner_fit", "owner_validate", "owner_resume"))
        unit_deps = [] if (fold, seed) == PILOT else [gate.key]
        deps[fit.key] = unit_deps
        deps[validate.key] = [fit.key]
        deps[resume.key] = [validate.key]
        tasks += [fit, validate, resume]
        for block in range(BLOCKS):
            run, check, again = Task("run", fold, seed, block), Task("validate", fold, seed, block), Task("resume", fold, seed, block)
            deps[run.key] = [validate.key]
            deps[check.key] = [run.key]
            deps[again.key] = [check.key]
            tasks += [run, check, again]
        if (fold, seed) == PILOT:
            deps[gate.key] = [t.key for t in tasks]
            tasks.append(gate)
    final = Task("aggregate")
    deps[final.key] = [t.key for t in tasks]
    tasks.append(final)
    return tasks, deps


def scientific_process(proc: psutil.Process) -> psutil.Process:
    """The venv launcher is a stub; the interpreter is its python child."""
    try:
        children = [c for c in proc.children(recursive=True) if "python" in c.name().lower()]
        return children[-1] if children else proc
    except psutil.Error:
        return proc


def orphan_workers() -> list[dict]:
    """Live scientific processes of this extension not started by this supervisor."""
    found = []
    scripts = ("hc_owner.py", "hc_adapter.py", "hc_validate.py", "hc_pilot_gate.py", "hc_aggregate.py")
    for process in psutil.process_iter(["pid", "cmdline", "ppid"]):
        try:
            cmdline = " ".join(process.info["cmdline"] or [])
        except psutil.Error:
            continue
        if str(HERE).lower() in cmdline.lower() and any(s in cmdline for s in scripts):
            if process.info["ppid"] != os.getpid():
                found.append({"pid": process.info["pid"], "cmdline": cmdline[-300:]})
    return found


def quarantine_partials(task: Task) -> list[str]:
    moved = []
    if task.kind in ("run", "resume"):
        parent = task.stage.parent
        for partial in parent.glob(task.stage.name + ".partial-*"):
            pid = int(partial.name.rsplit("-", 1)[-1]) if partial.name.rsplit("-", 1)[-1].isdigit() else None
            if pid is not None and psutil.pid_exists(pid):
                continue
            target = QUARANTINE / task.unit / f"{partial.name}_{int(time.time())}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(partial), str(target))
            moved.append(str(target))
    if moved:
        event("quarantined_partials", task=task.key, moved=moved)
    return moved


class Supervisor:
    def __init__(self) -> None:
        self.tasks, self.deps = build_tasks()
        self.by_key = {t.key: t for t in self.tasks}
        self.running: dict[str, dict] = {}
        self.attempts: dict[str, int] = {}
        self.not_before: dict[str, float] = {}
        self.durations: dict[str, list[float]] = {}
        self.started = utc()
        self.state = "running"
        self.error = None
        self.last_pause_event = 0.0
        self.peak_rss = 0
        self.min_ram = None
        self.min_commit = None
        self.min_disk = None
        self.done_cache: set[str] = set()

    def control(self) -> dict:
        value = {"max_workers": 1, "pause": False, "stop": False}
        if CONTROL.exists():
            try:
                value.update(read(CONTROL))
            except ValueError:
                pass
        value["max_workers"] = max(1, min(3, int(value["max_workers"])))
        return value

    def is_done(self, task: Task) -> bool:
        if task.key in self.done_cache:
            return True
        if task.done():
            self.done_cache.add(task.key)
            return True
        return False

    def ready(self) -> list[Task]:
        # Within one unit, at most one task per lane: owner tasks are exclusive; one
        # block run (the only writer of the unit ledger) may overlap with one
        # validation and one zero-fit resume of earlier blocks, which only read it.
        busy: dict[str, set[str]] = {}
        for key in self.running:
            running_task = self.by_key[key]
            busy.setdefault(running_task.unit, set()).add(lane(running_task.kind))
        out = []
        for task in self.tasks:
            if task.key in self.running or self.is_done(task):
                continue
            lanes = busy.get(task.unit, set())
            if "exclusive" in lanes or (lanes and lane(task.kind) == "exclusive") or lane(task.kind) in lanes:
                continue
            if time.time() < self.not_before.get(task.key, 0):
                continue
            if task.kind in ("pilot_gate", "aggregate") and self.running:
                continue
            if all(self.is_done(self.by_key[d]) for d in self.deps[task.key]):
                out.append(task)
        return out

    def launch(self, task: Task) -> None:
        attempt = self.attempts.get(task.key, 0) + 1
        self.attempts[task.key] = attempt
        if attempt > 1:
            quarantine_partials(task)
        ATTEMPTS.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out = ATTEMPTS / f"{task.key}_a{attempt}_{stamp}.stdout.log"
        err = ATTEMPTS / f"{task.key}_a{attempt}_{stamp}.stderr.log"
        before = tree(task.stage) if task.kind == "resume" else None
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
        stdout, stderr = out.open("w", encoding="utf-8"), err.open("w", encoding="utf-8")
        process = psutil.Popen(task.argv(attempt), cwd=str(FROZEN), stdout=stdout, stderr=stderr, env=env,
                               creationflags=subprocess.CREATE_NO_WINDOW)
        self.running[task.key] = {"process": process, "started": time.time(), "stdout": out, "stderr": err,
                                  "handles": (stdout, stderr), "before": before, "attempt": attempt, "peak_rss": 0}
        event("task_started", task=task.key, attempt=attempt, pid=process.pid, argv=task.argv(attempt))

    def finish(self, key: str, code: int) -> None:
        record = self.running.pop(key)
        for handle in record["handles"]:
            handle.close()
        task = self.by_key[key]
        elapsed = time.time() - record["started"]
        stderr = record["stderr"].read_text(encoding="utf-8", errors="replace")
        stdout = record["stdout"].read_text(encoding="utf-8", errors="replace")
        if task.kind == "resume":
            after = tree(task.stage)
            ok = code == 0 and after == record["before"] and "complete_zero_fit_resume" in stdout
            result = {"passed": ok, "exit_code": code, "files_unchanged": after == record["before"],
                      "status": "complete_zero_fit_resume" if "complete_zero_fit_resume" in stdout else None,
                      "models_fitted": 0, "fitting_disabled_during_resume": True, "utc": utc(),
                      "stdout": str(record["stdout"]), "stderr": str(record["stderr"])}
            write_json(UNITS / task.unit / "resume" / f"block_{task.block:03d}.json", result)
            if not ok:
                code = code or SCIENTIFIC_FAILURE_EXIT
        event("task_returned", task=key, attempt=record["attempt"], exit_code=code, seconds=round(elapsed, 2),
              peak_rss_bytes=record["peak_rss"])
        if code == 0 and task.done():
            self.done_cache.add(key)
            self.durations.setdefault(task.kind, []).append(elapsed)
            return
        scientific = (code == SCIENTIFIC_FAILURE_EXIT or "SCIENTIFIC_VALIDATION_FAILURE" in stderr
                      or "PILOT_GATE_FAILURE" in stderr + stdout)
        message = (stderr or stdout)[-4000:]
        if scientific or record["attempt"] >= MAX_ATTEMPTS:
            self.state = "blocked"
            self.error = {"task": key, "exit_code": code, "scientific": scientific, "attempts": record["attempt"],
                          "message": message}
            event("blocked", **self.error)
            return
        self.not_before[key] = time.time() + 60 * record["attempt"]
        event("retry_scheduled", task=key, attempt=record["attempt"], exit_code=code, message=message[-1500:])

    def poll(self) -> None:
        for key, record in list(self.running.items()):
            process = record["process"]
            try:
                worker = scientific_process(process)
                record["peak_rss"] = max(record["peak_rss"], int(worker.memory_info().rss))
                self.peak_rss = max(self.peak_rss, record["peak_rss"])
            except psutil.Error:
                pass
            code = process.poll()
            if code is not None:
                self.finish(key, code)
            elif time.time() - record["started"] > TIMEOUT_SECONDS[self.by_key[key].kind]:
                for child in process.children(recursive=True):
                    child.kill()
                process.kill()
                event("task_timeout", task=key)

    def headroom(self, running: int) -> tuple[bool, dict]:
        r = resources()
        self.min_ram = r["available_ram_bytes"] if self.min_ram is None else min(self.min_ram, r["available_ram_bytes"])
        self.min_commit = r["commit_available_bytes"] if self.min_commit is None else min(self.min_commit, r["commit_available_bytes"])
        self.min_disk = r["free_disk_bytes"] if self.min_disk is None else min(self.min_disk, r["free_disk_bytes"])
        floor = RAM_FLOOR_FIRST if running == 0 else RAM_FLOOR_ADDITIONAL
        ok = (r["available_ram_bytes"] >= floor and r["commit_available_bytes"] >= COMMIT_FLOOR
              and r["free_disk_bytes"] >= DISK_FLOOR)
        return ok, r

    def counts(self) -> dict:
        done = {kind: sum(1 for t in self.tasks if t.kind == kind and t.key in self.done_cache)
                for kind in ("owner_fit", "owner_validate", "owner_resume", "run", "validate", "resume")}
        accepted = done["resume"]
        return {"owners_fitted": done["owner_fit"], "owners_validated": done["owner_validate"],
                "owners_resumed": done["owner_resume"], "blocks_completed": done["run"],
                "blocks_validated": done["validate"], "blocks_zero_fit_resumed": accepted,
                "blocks_total": 495, "blocks_remaining": 495 - accepted,
                "evaluation_rows_accepted": accepted * 3, "evaluation_rows_remaining": (495 - accepted) * 3,
                "pilot_gate_passed": "pilot_gate" in self.done_cache,
                "aggregate_passed": "aggregate" in self.done_cache}

    def heartbeat(self, control: dict, r: dict, paused: bool) -> None:
        counts = self.counts()
        cycle = sum(sum(self.durations.get(k, [])) / max(1, len(self.durations.get(k, []))) for k in ("run", "validate", "resume"))
        measured = len(self.durations.get("run", []))
        workers = max(1, control["max_workers"])
        running = {}
        for key, record in self.running.items():
            running[key] = {"pid": record["process"].pid, "attempt": record["attempt"],
                            "seconds": round(time.time() - record["started"], 1), "peak_rss_bytes": record["peak_rss"]}
        write_json(STATUS, {
            "state": self.state, "paused_for_resources": paused, "supervisor_pid": os.getpid(),
            "supervisor_create_time": psutil.Process().create_time(), "started_utc": self.started,
            "heartbeat_utc": utc(), "control": control, "running": running, **counts,
            "measured_block_cycles": measured,
            "mean_seconds_per_block_cycle": round(cycle, 1) if measured else None,
            "estimated_remaining_seconds_at_current_workers":
                round(cycle * counts["blocks_remaining"] / workers) if measured else None,
            "resources": r, "minimum_available_ram_bytes": self.min_ram,
            "minimum_commit_available_bytes": self.min_commit, "minimum_free_disk_bytes": self.min_disk,
            "peak_scientific_rss_bytes": self.peak_rss, "error": self.error,
            "logs": {"events": str(EVENTS), "attempts": str(ATTEMPTS), "status": str(STATUS)},
        })

    def run(self) -> int:
        while orphans := orphan_workers():
            # A worker left by an earlier supervisor is still running; never duplicate it.
            event("orphan_worker_wait", workers=orphans)
            self.state = "waiting_for_orphan_worker"
            self.heartbeat(self.control(), resources(), False)
            time.sleep(60)
        self.state = "running"
        for task in self.tasks:
            self.is_done(task)
        event("supervisor_started", pid=os.getpid(), done=len(self.done_cache), tasks=len(self.tasks))
        while True:
            control = self.control()
            self.poll()
            paused = False
            r = resources()
            if self.state == "running" and not control["stop"] and not control["pause"]:
                while len(self.running) < control["max_workers"]:
                    candidates = self.ready()
                    if not candidates:
                        break
                    ok, r = self.headroom(len(self.running))
                    if not ok:
                        paused = True
                        if time.time() - self.last_pause_event > 600:
                            event("resource_pause", running=len(self.running), resources=r)
                            self.last_pause_event = time.time()
                        break
                    self.launch(candidates[0])
            self.heartbeat(control, r, paused)
            if not self.running:
                if self.state == "blocked":
                    event("supervisor_exit", state=self.state)
                    return 2
                if control["stop"]:
                    self.state = "stopped_by_control"
                    self.heartbeat(control, r, paused)
                    event("supervisor_exit", state=self.state)
                    return 0
                if all(t.key in self.done_cache for t in self.tasks):
                    self.state = "scientific_complete_delivery_pending"
                    self.heartbeat(control, r, paused)
                    event("supervisor_exit", state=self.state)
                    return 0
            time.sleep(POLL_SECONDS)


def acquire_lock() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    me = psutil.Process()
    record = {"pid": me.pid, "create_time": me.create_time(), "utc": utc(), "argv": sys.argv}
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                held = read(LOCK)
                alive = psutil.pid_exists(held["pid"]) and abs(psutil.Process(held["pid"]).create_time() - held["create_time"]) < 1
            except (ValueError, KeyError, psutil.Error):
                alive = False
            if alive:
                raise SystemExit(f"another supervisor holds the lock: {held}")
            stale = ROOT / "stale_locks" / f"supervisor.lock.{int(time.time())}"
            stale.parent.mkdir(parents=True, exist_ok=True)
            os.replace(LOCK, stale)
            event("stale_lock_preserved", path=str(stale))
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(record))
        return


def release_lock() -> None:
    try:
        held = read(LOCK)
        if held.get("pid") == os.getpid():
            LOCK.unlink()
    except (OSError, ValueError):
        pass


def verify_self() -> None:
    protocol = read(HERE / "EXTENSION_PROTOCOL.json")
    content = (HERE / "hc_supervisor.py").read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(content).hexdigest() != protocol["orchestration_code_lf_sha256"]["hc_supervisor.py"]:
        raise SystemExit("supervisor code differs from the frozen extension protocol")


def launch_detached() -> None:
    if LOCK.exists():
        try:
            held = read(LOCK)
            if psutil.pid_exists(held["pid"]) and abs(psutil.Process(held["pid"]).create_time() - held["create_time"]) < 1:
                raise SystemExit(f"supervisor already running: pid {held['pid']}")
        except (ValueError, KeyError, psutil.Error):
            pass
    ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = (ROOT / f"supervisor_{stamp}.stdout.log").open("w", encoding="utf-8")
    err = (ROOT / f"supervisor_{stamp}.stderr.log").open("w", encoding="utf-8")
    flags = 0x00000008 | 0x00000200 | 0x01000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | BREAKAWAY_FROM_JOB
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "run"], cwd=str(HERE),
                               stdout=out, stderr=err, stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    print(json.dumps({"launched_pid": process.pid, "stdout": out.name, "stderr": err.name}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run", "launch", "status"])
    args = parser.parse_args()
    if args.action == "status":
        print(STATUS.read_text(encoding="utf-8") if STATUS.exists() else "no status")
        return 0
    if args.action == "launch":
        verify_self()
        launch_detached()
        return 0
    verify_self()
    acquire_lock()
    try:
        return Supervisor().run()
    except Exception as exc:  # recorded, then re-raised for the stderr log
        event("supervisor_crashed", error=repr(exc))
        raise
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
