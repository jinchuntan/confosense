"""Durable single-instance coordinator for the interrupted PLEIA-temperature C pilot.

Preserves the failed 2026-09-18 coordinator (coordinator.py) and its receipts.
Standalone: stdlib + psutil only, so no energy module with top-level side effects
is imported into this temperature unit.

Responsibilities:
  * run one phase at a time from an externally readable plan file
  * re-read the plan before each phase so phases can be appended without ever
    launching a second coordinator
  * record liveness (heartbeat), phase transitions, and an exit/failure receipt
    for every attempt, including nonzero exits, which are never reclassified here
  * track the real scientific worker, not just the venv redirector stub
"""
import json, os, subprocess, sys, time
from pathlib import Path

import psutil

REVIEW = Path(__file__).resolve().parent
REPO = REVIEW.parents[1]
SMART = REPO / 'smart_building_conformal'
COORD = SMART / 'outputs/conditional_context005/pleia_temperature_f2_context005_pilot_v1_coordinator'
RUN = SMART / 'outputs/conditional_context005/pleia_f2_s42_C_v1'

PLAN = COORD / 'PHASE_PLAN.json'
STATE = COORD / 'DURABLE_COORDINATOR_STATE.json'
HEARTBEAT = COORD / 'DURABLE_COORDINATOR_HEARTBEAT.json'
ATTEMPTS = COORD / 'durable_attempts.jsonl'
LOCK = COORD / 'DURABLE_COORDINATOR_LOCK.json'

HEARTBEAT_SECONDS = 15


def now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + os.urandom(8).hex() + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')
    os.replace(tmp, path)


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, default=str) + '\n')
        f.flush()
        os.fsync(f.fileno())


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def stage_progress():
    """Checkpoint-based progress, so a slow phase is diagnosed by work done."""
    stages = RUN / 'stages'
    if not stages.exists():
        return dict(committed_stages=0, contexts_complete=0)
    names = [p.name for p in stages.iterdir() if p.is_dir()]
    ctx = [n for n in names if n.startswith('context_')]
    return dict(committed_stages=len(names), context_stages=len(ctx),
                contexts_complete=len(ctx) // 43, complete_json=(RUN / 'COMPLETE.json').exists())


def claim_lock():
    """Refuse to become a duplicate coordinator."""
    if LOCK.exists():
        try:
            held = read(LOCK)
        except Exception:
            held = None
        if held:
            pid = held.get('pid')
            if pid and psutil.pid_exists(pid):
                try:
                    p = psutil.Process(pid)
                    if p.create_time() == held.get('create_time') and 'durable_coordinator.py' in ' '.join(p.cmdline()):
                        print('another durable coordinator is alive; refusing to duplicate', flush=True)
                        raise SystemExit(3)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    me = psutil.Process(os.getpid())
    atomic(LOCK, dict(pid=os.getpid(), create_time=me.create_time(), started_utc=now(),
                      cmdline=me.cmdline()))


def descendant_worker(proc):
    """The venv Scripts/python.exe is a redirector; the real worker is a child."""
    try:
        for child in proc.children(recursive=True):
            try:
                if 'conditional_context005' in ' '.join(child.cmdline()):
                    return child
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
    return None


def run_phase(phase):
    name = phase['name']
    argv = phase['argv']
    log = COORD / f'phase_{name}.log'
    started = dict(event='phase_started', phase=name, argv=argv, cwd=str(SMART),
                   utc=now(), coordinator_pid=os.getpid(), log=str(log),
                   progress_before=stage_progress())
    append(ATTEMPTS, started)
    atomic(COORD / f'phase_{name}.started.json', started)

    with open(log, 'ab') as sink:
        sink.write(f'\n=== phase {name} started {now()} ===\n'.encode())
        sink.flush()
        proc = subprocess.Popen(argv, cwd=str(SMART), stdout=sink,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        parent = psutil.Process(proc.pid)
        worker = None
        peak_rss = 0
        cpu = 0.0
        while proc.poll() is None:
            # Re-resolve until the real worker is found: the venv redirector stub
            # matches the command line too, so latching onto it would under-report.
            if worker is None or not worker.is_running() or worker.pid == proc.pid:
                try:
                    fallback = parent if 'conditional_context005' in ' '.join(parent.cmdline()) else None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    fallback = None
                worker = descendant_worker(parent) or fallback
            wpid = None
            if worker is not None:
                try:
                    wpid = worker.pid
                    mem = worker.memory_info()
                    peak_rss = max(peak_rss, mem.rss)
                    cpu = worker.cpu_times().user + worker.cpu_times().system
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            atomic(HEARTBEAT, dict(utc=now(), coordinator_pid=os.getpid(), phase=name,
                                   launcher_pid=proc.pid, worker_pid=wpid,
                                   worker_cpu_seconds=round(cpu, 2),
                                   worker_peak_rss_bytes=peak_rss,
                                   progress=stage_progress()))
            time.sleep(HEARTBEAT_SECONDS)
        code = proc.wait()

    finished = dict(event='phase_finished', phase=name, argv=argv, exit_status=code,
                    utc=now(), coordinator_pid=os.getpid(), log=str(log),
                    worker_peak_rss_bytes=peak_rss, worker_cpu_seconds=round(cpu, 2),
                    progress_after=stage_progress())
    append(ATTEMPTS, finished)
    atomic(COORD / f'phase_{name}.finished.json', finished)
    return code


def main():
    claim_lock()
    state = read(STATE) if STATE.exists() else dict(completed_phases=[], started_utc=now())
    append(ATTEMPTS, dict(event='coordinator_started', pid=os.getpid(), utc=now(),
                          completed_phases=list(state['completed_phases'])))
    while True:
        plan = read(PLAN)['phases']
        pending = [p for p in plan if p['name'] not in state['completed_phases']]
        if not pending:
            atomic(STATE, dict(state, status='all_planned_phases_complete', updated_utc=now()))
            atomic(HEARTBEAT, dict(utc=now(), coordinator_pid=os.getpid(),
                                   phase='idle_all_complete', progress=stage_progress()))
            append(ATTEMPTS, dict(event='coordinator_idle_all_phases_complete', pid=os.getpid(), utc=now()))
            break
        phase = pending[0]
        atomic(STATE, dict(state, status='running', current_phase=phase['name'], updated_utc=now()))
        code = run_phase(phase)
        if code != 0:
            atomic(STATE, dict(state, status='phase_failed', current_phase=phase['name'],
                               exit_status=code, updated_utc=now()))
            append(ATTEMPTS, dict(event='coordinator_stopped_on_failure', phase=phase['name'],
                                  exit_status=code, pid=os.getpid(), utc=now()))
            atomic(HEARTBEAT, dict(utc=now(), coordinator_pid=os.getpid(),
                                   phase='stopped_failed:' + phase['name'], exit_status=code,
                                   progress=stage_progress()))
            raise SystemExit(code)
        state['completed_phases'].append(phase['name'])
        atomic(STATE, dict(state, status='phase_complete', current_phase=phase['name'], updated_utc=now()))
    atomic(HEARTBEAT, dict(utc=now(), coordinator_pid=os.getpid(), phase='exited_clean',
                           progress=stage_progress()))


if __name__ == '__main__':
    main()
