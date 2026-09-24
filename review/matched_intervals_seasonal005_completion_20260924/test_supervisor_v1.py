from pathlib import Path
import tempfile
import unittest

import supervisor_v1 as supervisor


def progress(status="running", failure=None, completed=5):
    return {"status": status, "failure": failure, "completed_bundles": completed}


class SupervisorTests(unittest.TestCase):
    def test_duplicate_launch_prevention_and_adoption(self):
        script = Path("C:/work/coordinator.py")
        rows = [
            {"pid": 10, "ppid": 1, "command": f'python "{script}" --run'},
            {"pid": 11, "ppid": 10, "command": f'python "{script}" --run'},
        ]
        self.assertEqual(len(supervisor.process_families(rows, script, "--run")), 1)
        action, _ = supervisor.choose_action(
            progress=progress(), coordinator_count=1, worker_count=0, finalizer_count=0,
            delivery_complete=False, recovery_ready=False, retries=0,
            finalizer_started=False, free_bytes=supervisor.DISK_FLOOR + 1)
        self.assertEqual(action, "running")
        action, _ = supervisor.choose_action(
            progress=progress(), coordinator_count=2, worker_count=0, finalizer_count=0,
            delivery_complete=False, recovery_ready=False, retries=0,
            finalizer_started=False, free_bytes=supervisor.DISK_FLOOR + 1)
        self.assertEqual(action, "block")

    def test_recorded_failure_detection(self):
        self.assertEqual(supervisor.failure_class(progress("blocked", "unexpected process exit")),
                         "recorded_failure")

    def test_bounded_recoverable_retry(self):
        failed = progress("blocked", "ModuleNotFoundError: No module named 'src'")
        for retries, expected in ((0, "launch_coordinator"), (1, "launch_coordinator"), (2, "block")):
            action, _ = supervisor.choose_action(
                progress=failed, coordinator_count=0, worker_count=0, finalizer_count=0,
                delivery_complete=False, recovery_ready=True, retries=retries,
                finalizer_started=False, free_bytes=supervisor.DISK_FLOOR + 1)
            self.assertEqual(action, expected)

    def test_recorded_import_attempt_is_recoverable_only_by_exact_identity(self):
        failed = progress("blocked", "phase bdg2_f1_s42/validate_decimal_rank_v1 failed; actual exit 1")
        self.assertEqual(supervisor.failure_class(failed), "recoverable_import")

    def test_hard_validation_blocks(self):
        failed = progress("blocked", "bundle validation/resume failed: bdg2_f1_s42")
        self.assertEqual(supervisor.failure_class(failed), "hard_validation")
        action, _ = supervisor.choose_action(
            progress=failed, coordinator_count=0, worker_count=0, finalizer_count=0,
            delivery_complete=False, recovery_ready=True, retries=0,
            finalizer_started=False, free_bytes=supervisor.DISK_FLOOR + 1)
        self.assertEqual(action, "block")

    def test_finalizer_failure_detection(self):
        action, reason = supervisor.choose_action(
            progress=progress("science_validated", completed=52), coordinator_count=0,
            worker_count=0, finalizer_count=0, delivery_complete=False,
            recovery_ready=True, retries=1, finalizer_started=True,
            free_bytes=supervisor.DISK_FLOOR + 1)
        self.assertEqual(action, "block")
        self.assertIn("finisher exited", reason)

    def test_unexpected_running_coordinator_absence_requires_reconciliation(self):
        action, reason = supervisor.choose_action(
            progress=progress("running"), coordinator_count=0, worker_count=0,
            finalizer_count=0, delivery_complete=False, recovery_ready=True,
            retries=0, finalizer_started=False, free_bytes=supervisor.DISK_FLOOR + 1)
        self.assertEqual(action, "block")
        self.assertIn("ledger reconciliation", reason)

    def test_delivery_waits_for_finisher_exit(self):
        action, _ = supervisor.choose_action(
            progress=progress("science_validated", completed=52), coordinator_count=0,
            worker_count=0, finalizer_count=1, delivery_complete=True,
            recovery_ready=True, retries=1, finalizer_started=True,
            free_bytes=supervisor.DISK_FLOOR + 1)
        self.assertEqual(action, "finalizing")

    def test_atomic_status_and_single_event_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            old_root, old_status, old_events = supervisor.ROOT, supervisor.STATUS, supervisor.EVENTS
            try:
                supervisor.ROOT = Path(temporary)
                supervisor.STATUS = supervisor.ROOT / "status.json"
                supervisor.EVENTS = supervisor.ROOT / "events.jsonl"
                supervisor.atomic(supervisor.STATUS, {"state": "running"})
                supervisor.event("fixture")
                self.assertEqual(supervisor.read(supervisor.STATUS)["state"], "running")
                self.assertEqual(len(supervisor.EVENTS.read_text().splitlines()), 1)
            finally:
                supervisor.ROOT, supervisor.STATUS, supervisor.EVENTS = old_root, old_status, old_events


if __name__ == "__main__":
    unittest.main()
