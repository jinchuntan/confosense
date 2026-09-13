"""Durable preflight -> tests -> evaluated commits -> sequential 52-unit batch."""
import re, time
from common import *
from coordinator import Engine, exclusive_lock, progress, verify_frozen, identity, alive, family

def main():
    os.chdir(SMART)
    with exclusive_lock(BACKUP/'bootstrap.lock'):
        prep=BATCH/'prepare_command_v1.log.json'
        print('Waiting for the already launched no-fit preparation; no model fitting yet.',flush=True)
        started=read(BATCH/'prepare_command_v1.log.started.json')
        identities=family(started['logger_pid']) if not prep.exists() else []
        watch_stamp=now().replace(':','').replace('.','')
        atomic(BACKUP/f'bootstrap_preparation_watch_{watch_stamp}.json',dict(utc=now(),preparation_started=started,process_identities=identities))
        while not prep.exists():
            if not any(alive(record) for record in identities):
                time.sleep(2)
                assert prep.exists(), 'preparation processes ended without an actual exit receipt; inspect and preserve partial preflight'
            time.sleep(2)
        result=read(prep)
        assert result['exit_status']==0, 'preparation failed; inspect preserved receipt before continuing'
        assert git('branch','--show-current')==BRANCH
        manifest=read(REVIEW/'joint_pre_fit_manifest.json');verify_frozen(manifest)
        command=[PYTHON,'-B','-m','pytest',str(REVIEW/'test_coordinator.py'),'tests/test_matched005_partition_guard.py','tests/test_matched005_identifier_export.py','tests/test_matched_forecasting005.py','-k','not tiny_matched_checkpoint_integration','-q']
        testlog=BATCH/'regression_v1.log'
        if Path(str(testlog)+'.json').exists():
            prior=read(str(testlog)+'.json');assert prior['exit_status']==0 and prior['command']==command
        else:logged(command,testlog)
        output=testlog.read_text(encoding='utf-8');counts=re.findall(r'(\d+) passed',output)
        # Repository pytest options suppress the prose summary at this quiet
        # level. The actual exit-0 receipt plus 30 pass dots at 100% is complete.
        quiet=re.findall(r'^([.]+)\s+\[100%\]\s*$',output,re.MULTILINE)
        passed=int(counts[-1]) if counts else len(quiet[-1]) if quiet else None
        assert passed==30,output[-1500:]
        assert read(BATCH/'diagnosis_v2/validation.json')['models_fitted']==0
        text='# Evaluated pre-fit record\n\nAll 52 exact fold-2 keys at seeds 43–46 were frozen and passed fresh no-fit readiness before any learned fit. Cross-seed data, ordered memberships, boundaries, schema, packages and non-seed scientific settings match the corresponding preserved seed-42 unit. The new authorization binds the current handoff separately from historical runner provenance.\n\n'
        text+='The bounded diagnosis completed with zero fitting and found no unresolved correctness defect. Its first attempt rejected floating-point endpoint ties; the corrected diagnostic uses the actual saved inclusive bounds, verifies ties within floating precision and leaves all historical metrics unchanged. Both attempts are retained.\n\n'
        text+='Thirty focused checks passed: fifteen existing scientific-integrity checks plus fifteen dummy coordinator/seed/summary checks. No tiny learned fit was performed. Tests cover ordering, failed-validation stopping, live-worker adoption, completed restart, locks/PID reuse, atomic rename failure handling, exact new scope, NumPy/Torch/shuffle seed propagation, rejecting a mislabeled fit seed, and signed versus absolute coverage deviations/sample SD.\n\n'
        text+='The reused coordinator is isolated in this new directory and new output/backup paths. It runs each unit, independent metric/model validation, completed forbidden-fit resume, group reconciliation and actual seed verification before advancing. Seed boundaries trigger aggregate reports, commits, verified external bundles and publication attempts; authentication alone cannot stop authorized science. Final aggregation runs automatically after seed 46.\n\n'
        text+='Scientific source SHA-256: `'+manifest['source_hash']+'`. Frozen scope planning scenario: '+f'{manifest["scenario_low_model_hours"]:.4f}–{manifest["scenario_high_model_hours"]:.4f} model-hours, excluding preparation/I/O/verification; not a statistical interval or deadline. CPU-only one-thread execution, lazy batch256, nonblocking 3 GiB launch reference, 256 MiB epoch floor and 8 GiB free disk are unchanged.\n'
        atomic(REVIEW/'PRE_FIT_RECORD.md',text)
        engine=Engine(BATCH);progress(engine,manifest)
        import publish
        if not (REVIEW/'evaluated_commit.json').exists():
            publish.main('prefit')
            atomic(REVIEW/'evaluated_commit.json',dict(commit=git('rev-parse','HEAD'),source_hash=manifest['source_hash'],entry_commit=ENTRY,all_52_ready_before_fit=True,regression_checks=30,tiny_fits=0,diagnosis_models_fitted=0,helper_hashes={p.name:sha(p) for p in sorted(REVIEW.glob('*.py'))}))
            publish.main('prefit_record')
        else:
            subprocess.run(['git','merge-base','--is-ancestor',read(REVIEW/'evaluated_commit.json')['commit'],'HEAD'],cwd=ROOT,check=True)
        print('Preflight, diagnosis, tests and evaluated commits complete. Starting the entire authorized batch.',flush=True)
        stamp=now().replace(':','').replace('.','')
        logged([PYTHON,'-B',str(REVIEW/'coordinator.py')],BACKUP/f'coordinator_{stamp}.log')
        print('AUTHORIZED 52-UNIT BATCH AND AUTOMATIC REPORTS FINISHED',flush=True)

if __name__=='__main__':main()
