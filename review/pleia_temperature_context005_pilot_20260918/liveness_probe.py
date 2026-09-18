"""Independent durable liveness recorder for the temperature pilot.

Supervisory only: it never touches scientific state and never signals any
process. It exists because a launch receipt is not evidence of continuing
supervision, and because the coordinator heartbeat can latch onto the venv
redirector stub instead of the real interpreter.

Appends one JSON line per sample identifying the coordinator, the redirector
stub and the real scientific worker by PID + creation time + command line,
together with checkpoint progress so a slow phase is diagnosed by work done
rather than by elapsed time alone.
"""
import datetime, json, os, time
from pathlib import Path

import psutil

REVIEW = Path(__file__).resolve().parent
REPO = REVIEW.parents[1]
SMART = REPO / 'smart_building_conformal'
COORD = SMART / 'outputs/conditional_context005/pleia_temperature_f2_context005_pilot_v1_coordinator'
RUN = SMART / 'outputs/conditional_context005/pleia_f2_s42_C_v1'
LOG = COORD / 'liveness_probe.jsonl'

INTERVAL = 60
LIMIT = 60 * 60 * 14 // INTERVAL


def iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat()


def describe(p):
    try:
        t = p.cpu_times()
        return dict(pid=p.pid, ppid=p.ppid(), created_utc=iso(p.create_time()),
                    cpu_seconds=round(t.user + t.system, 2),
                    rss_bytes=p.memory_info().rss,
                    exe=p.exe(), cmdline=' '.join(p.cmdline())[:240])
    except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
        return dict(pid=p.pid, error=type(exc).__name__)


def scan():
    coordinator = stub = worker = None
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if not (p.info['name'] or '').lower().startswith('python'):
                continue
            cl = ' '.join(p.info['cmdline'] or [])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if 'durable_coordinator.py' in cl:
            coordinator = p
        elif 'src.conditional_context005' in cl:
            try:
                exe = p.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            # The redirector lives under the venv Scripts directory.
            if 'cfs_venv' in exe.replace('\\', '/'):
                stub = p
            else:
                worker = p
    return coordinator, stub, worker


def progress():
    stages = RUN / 'stages'
    if not stages.exists():
        return dict(committed_stages=0)
    names = [p.name for p in stages.iterdir() if p.is_dir()]
    ctx = [n for n in names if n.startswith('context_')]
    return dict(committed_stages=len(names), context_stages=len(ctx),
                contexts_complete=len(ctx) // 43, contexts_total=68,
                stages_expected=2929, complete_json=(RUN / 'COMPLETE.json').exists(),
                partials=len(list(RUN.glob('.partial_*'))))


def main():
    peak = 0
    for _ in range(LIMIT):
        coordinator, stub, worker = scan()
        if worker is not None:
            try:
                peak = max(peak, worker.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        state = None
        sp = COORD / 'DURABLE_COORDINATOR_STATE.json'
        if sp.exists():
            try:
                state = json.loads(sp.read_text(encoding='utf-8'))
            except Exception:
                state = None
        row = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   probe_pid=os.getpid(),
                   coordinator=describe(coordinator) if coordinator else None,
                   redirector_stub=describe(stub) if stub else None,
                   scientific_worker=describe(worker) if worker else None,
                   observed_worker_peak_rss_bytes=peak,
                   coordinator_state=state,
                   progress=progress())
        with LOG.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row) + '\n')
            f.flush()
            os.fsync(f.fileno())
        if coordinator is None and worker is None and state and state.get('status') in (
                'all_planned_phases_complete', 'phase_failed'):
            break
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
