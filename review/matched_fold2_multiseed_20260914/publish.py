"""Publish isolated multiseed artifacts with exact byte checks and external backup."""
import argparse, subprocess
from pathlib import Path
from common import *

def index(manifest,state):
    done=state.get('units',{});count=sum(bool(v.get('validated')) for v in done.values())
    text='# Matched fold-2 multiseed evidence index\n\n'+f'Validated {count}/52 new units. Scientific source SHA-256: `{manifest["source_hash"]}`. Entry commit `{ENTRY}`. [Authorizing handoff](AUTHORIZING_HANDOFF.md); [frozen scope](frozen_scope.csv); [joint pre-fit manifest](joint_pre_fit_manifest.json); [source archive](evaluated_source.zip); [seed path probes](seed_path_preflight.json); [cross-seed support](cross_seed_support.csv).\n\n'
    if (REVIEW/'evaluated_commit.json').exists():text+='[Evaluated pre-fit commit](evaluated_commit.json). '
    text+='[Progress and exact restart](PROGRESS_AND_RESTART.md). [Failure diagnosis](../../MATCHED_FAILURE_DIAGNOSIS.md), [diagnostic source tables](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2), [diagnostic validation](../../smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/validation.json). The first diagnostic attempt is retained separately; floating-point boundary ties were resolved by using the saved inclusive endpoints.\n\n'
    if (ROOT/'MATCHED_METHOD_READINESS_MAP.md').exists():text+='[Broader-method and alert implementation readiness](../../MATCHED_METHOD_READINESS_MAP.md).\n\n'
    text+='[Pre-fit regression record](PRE_FIT_RECORD.md), [bootstrap receipt-parser recovery](BOOTSTRAP_OUTPUT_RECOVERY.md), and [reporting-only corrections](REPORTING_NOTES.md) distinguish orchestration issues from scientific outcomes.\n\n'
    if (REVIEW/'delivery_v1/COMPLETION_VERIFICATION.md').exists():text+='[Final actual exit receipts, preservation and delivery verification](delivery_v1/COMPLETION_VERIFICATION.md).\n\n'
    if (REVIEW/'delivery_v1/REMOTE_VERIFICATION.json').exists():text+='[Published delivery verification](delivery_v1/REMOTE_VERIFICATION.json): exact remote tree/blob checks and 503 representative downloads at the pinned delivery commit; [actual verification exit receipt](delivery_v1/remote_verification_v1.log.json). The later receipt-publication commit retains those scientific blobs and is checked by [verify_delivery_seal.py](verify_delivery_seal.py).\n\n'
    if (REVIEW/'delivery_v1/final_checks_v1/validation.json').exists():text+='[Both-level Panel-2 comparison](delivery_v1/final_checks_v1/panel2_both_levels.csv), [final arithmetic/source checks](delivery_v1/final_checks_v1/validation.json), and [clearer cost figure](delivery_v1/cost_figure_v3/cost_and_error.png) ([PDF](delivery_v1/cost_figure_v3/cost_and_error.pdf), [source hashes](delivery_v1/cost_figure_v3/sources.json)). Earlier plot versions remain preserved.\n\n'
    if (ROOT/'MATCHED_FOLD2_MULTISEED_REPORT.md').exists():text+='[Current report](../../MATCHED_FOLD2_MULTISEED_REPORT.md); [Panel 2 response](PANEL2_NUMERICAL_RESPONSE.md).\n\n'
    dirs=sorted(BATCH.glob('seed*_summary_v1'))
    if (BATCH/'analysis_v1/COMPLETE.json').exists():dirs.append(BATCH/'analysis_v1')
    for directory in dirs:
        if not (directory/'COMPLETE.json').exists():continue
        prefix='../../'+directory.relative_to(ROOT).as_posix()+'/'
        text+='## '+directory.name+'\n\n'
        for file,label in [('combined_comparison.csv','Cumulative comparison with original identities'),('new_only_comparison.csv','New units only'),('fold2_five_seed_comparison.csv','Every fold-2 training seed; no best-seed selection'),('interval_quality.csv','Own 90/95 coverage, signed/absolute deviations, MPIW, Winkler'),('training_seed_summary.csv','Mean, sample SD, min/max on the same evaluation support'),('paired_model_contrasts.csv','Within-seed LSTM/XGBoost/persistence contrasts'),('actual_seed_metadata.csv','Fit records, estimator and serialized training seeds'),('group_metrics.csv','Original-run/building metrics and counts'),('rico_phase_metrics.csv','RICO acquisition-phase metrics and support'),('equal_group_diagnostics.csv','Separate equal-group diagnostics'),('model_costs.csv','Model-phase CPU/wall, memory, inference and serialization'),('run_costs.csv','New execution, preparation, validation/resume and memory costs'),('fold2_all_seed_run_costs.csv','Historical and new fold-2 command costs'),('seed_block_costs.csv','Measured seed-block sums'),('verification_summary.csv','Actual exits, metric/model checks and zero-fit resumes'),('fit_attempts.csv','Actual fitting starts/completions'),('command_attempts.csv','Durable argv/PIDs/times/exits'),('evidence_reuse_ledger.csv','Original run/source/protocol identities; no historical refits'),('completion_overlay.csv','Current completion over preserved matrix'),('remaining_queue_updated.csv','Exact remaining units and timing scenarios'),('panel2_horizon_summary.csv','All-seed interval/point/CPU trade-offs'),('analysis_validation.json','Reconciled actual completion counts')]:
            text+=f'- [{file}]({prefix}{file}): {label}.\n'
        if (directory/'figures').exists():
            text+='\nFigures (PNG, PDF and source-CSV/hash sidecars):\n\n'
            for name in ['forecast_error','coverage','interval_width','winkler','cost_and_error']:text+=f'- {name}: [PNG]({prefix}figures/{name}.png), [PDF]({prefix}figures/{name}.pdf), [sources]({prefix}figures/{name}.sources.json).\n'
    text+='\n## Per-unit artifacts\n\n'
    for u in manifest['units']:
        design='../../'+Path(u['design']).relative_to(ROOT).as_posix();run='../../'+Path(u['run']).relative_to(ROOT).as_posix();completed=done.get(u['stem'],{})
        text+='- '+u['stem']+f': [protocol]({design}/frozen_protocol.json), [membership]({design}/membership.csv.gz), [readiness]({design}/readiness.json). '
        if completed.get('validated'):
            audit='../../'+Path(completed['audit']).relative_to(ROOT).as_posix();resume='../../'+Path(completed['resume']).relative_to(ROOT).as_posix()
            text+=f'[Point metrics]({run}/point_summary.csv), [interval metrics]({run}/interval_quality.csv), [fitted models/all streams]({run}/units), [independent validation]({audit}/validation.json), [saved-model checks]({audit}/saved_model_verification.csv), [zero-fit resume]({resume}).\n'
        else:text+='Pending; actual status is in the progress ledger.\n'
    text+='\n## Preservation and recomputation\n\n[Byte manifest](EVIDENCE_MANIFEST.csv) covers the current task artifacts except itself; the Git commit binds it. [Dataset notices](DATA_NOTICE.md) retain attribution. Historical helpers and runs are unchanged. Each publication stages exact bytes under -text attributes, verifies Git blobs, commits and creates an external incremental bundle; authentication failure is recorded without stopping authorized science.\n\nAfter all 52 units complete, reproduce final arithmetic without fitting from the original repository root. Use an unused directory below this repository because generated links require a repository-relative output path. This also regenerates current reports/status; source runs and earlier analysis directories remain unchanged. Saved execution manifests retain their original absolute paths, so this command describes the original local layout.\n\n```powershell\n& C:/cfs_venv/Scripts/python.exe -B review/matched_fold2_multiseed_20260914/analyze.py final --out (Join-Path (Get-Location) \'smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/recomputed_analysis_v1\')\n```\n'
    atomic(REVIEW/'EVIDENCE_INDEX.md',text)

def package(manifest,state):
    index(manifest,state)
    for row in read(REVIEW/'entry_preservation.json')['files']:
        if row['path'] not in ['.gitattributes','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
            assert sha(ROOT/row['path'])==row['sha256'], 'historical file changed: '+row['path']
    paths=[REVIEW,AUTH,BATCH,ROOT/'.gitattributes']
    for u in manifest['units']:
        paths.append(Path(u['design']))
        run=Path(u['run'])
        if run.exists():paths.append(run)
        proc=Path(str(run)+'.process.json')
        if proc.exists():paths.append(proc)
    for name in ['MATCHED_FOLD2_MULTISEED_REPORT.md','MATCHED_FAILURE_DIAGNOSIS.md','MATCHED_METHOD_READINESS_MAP.md','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
        if (ROOT/name).exists():paths.append(ROOT/name)
    active=Path(state['active']['attempt_record']).parent if state.get('active') else None
    files=sorted(set(p for path in paths for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.tmp','.pyc'] and p.name!='EVIDENCE_MANIFEST.csv' and not (active and p.is_relative_to(active))))
    rows=[]
    for p in files:
        assert p.stat().st_size<100*2**20, 'oversized file requires lossless parts: '+str(p)
        rows.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    with (REVIEW/'EVIDENCE_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
    return [r['path'] for r in rows]+[(REVIEW/'EVIDENCE_MANIFEST.csv').relative_to(ROOT).as_posix()]

def main(label):
    assert git('branch','--show-current')==BRANCH
    assert git('rev-parse','main')=='06fe967be2be8d7898812c0c2d6e464d4e942351'
    manifest=read(REVIEW/'joint_pre_fit_manifest.json');state=read(BATCH/'progress.json')
    paths=package(manifest,state)
    pathfile=BACKUP/f'{label}_stage_paths.txt';atomic(pathfile,'\n'.join(paths)+'\n')
    subprocess.run(['git','add','--pathspec-from-file='+str(pathfile)],cwd=ROOT,check=True)
    # Previously staged text can retain an old normalized blob after -text is
    # added. Reapply the current attributes to this bounded evidence path list.
    subprocess.run(['git','add','--renormalize','--pathspec-from-file='+str(pathfile)],cwd=ROOT,check=True)
    staged={}
    for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0'):
        if entry:
            metadata,name=entry.split(b'\t',1)
            staged[name.decode('utf-8')]=metadata.split()[1].decode('ascii')
    for name in paths:
        data=(ROOT/name).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()
        assert staged[name]==blob, 'staged evidence bytes differ from manifest: '+name
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
        subprocess.run(['git','commit','-m',f'Publish matched fold-2 multiseed evidence: {label}'],cwd=ROOT,check=True)
    commit=git('rev-parse','HEAD');bundle=BACKUP/f'{label}_{commit[:7]}.bundle'
    if not bundle.exists():subprocess.run(['git','bundle','create',str(bundle),BRANCH,'^'+ENTRY],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    receipt=dict(label=label,utc=now(),branch=BRANCH,commit=commit,backup=str(bundle),backup_sha256=sha(bundle),local_science_preserved=True,publication_status='pending')
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    try:
        push=subprocess.run(['git','-c','credential.interactive=false','push','origin','HEAD:refs/heads/'+BRANCH],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60)
        receipt.update(push_exit=push.returncode,push_output=push.stdout)
        if push.returncode==0:
            refs=subprocess.check_output(['git','-c','credential.helper=','ls-remote','origin','refs/heads/'+BRANCH],cwd=ROOT,text=True,timeout=30)
            assert refs.startswith(commit+'\t');receipt['publication_status']='remote_sha_verified'
    except subprocess.TimeoutExpired:receipt['publication_error']='noninteractive publication timed out; local queue continues; Desktop publication can complete later'
    atomic(BACKUP/f'{label}_{commit[:7]}_publication.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();main(a.label)
