"""Commit bounded evidence, make an external bundle and attempt noninteractive push.

Publication-only authentication failures are recorded and never strand science.
"""
import argparse, os, shutil, subprocess, traceback, zipfile
from pathlib import Path
from common import *

def index(manifest,state):
    text='# Matched overnight batch evidence index\n\nScientific source SHA-256: `'+manifest['source_hash']+'`. Entry commit: `'+ENTRY+'`. [Authorization handoff](AUTHORIZING_HANDOFF.md); [joint pre-fit manifest](joint_pre_fit_manifest.json); [evaluated source archive](evaluated_source.zip); [evaluated commit](evaluated_commit.json); [ordered role support](fresh_role_support.csv).\n\n'
    text+='[Progress and exact restart instructions](PROGRESS_AND_RESTART.md). [Atomic progress ledger](../../smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/progress.json); [append-only attempts](../../smart_building_conformal/outputs/matched_forecasting005/overnight_batch_v1/attempts.jsonl). Every attempt records exact argv, process identities, actual exit and separate external validation/resume receipts.\n\n'
    final=BATCH/'analysis_v1'
    if (final/'COMPLETE.json').exists():
        text+='## Completed results\n\n[Full report](../../MATCHED_OVERNIGHT_BATCH_REPORT.md); [Panel 2 numerical response](PANEL2_NUMERICAL_RESPONSE.md).\n\n'
        purposes={'combined_comparison.csv':'All 54 model rows /18 paired units, own 90%/95% intervals, point errors and costs','new_only_comparison.csv':'36 model rows for these twelve new paired units','fold2_seed42_all_horizons.csv':'Main comparable slice: all13 task/horizon combinations,39 model rows','additional_folds_comparison.csv':'Separate historical fold0 and new BDG2 fold1 evidence','paired_model_contrasts.csv':'LSTM-minus-XGBoost and learned-minus-persistence errors, intervals, phase times, CPU and throughput ratios','group_metrics.csv':'Per-original-run/building point/interval summaries, negatives and RICO history','rico_phase_metrics.csv':'RICO acquisition-phase sample-weighted summaries and support','equal_group_diagnostics.csv':'Separate equal-group diagnostics; not relabelled pooled','model_costs.csv':'Measured model phases, CPU, throughput, serialization and memory','run_costs.csv':'Actual command wall/CPU, preparation, validation/resume, action/lifetime memory','checkpoint_io.csv':'Checkpoint serialization and I/O phase measurements','fit_attempts.csv':'Every actual learned-fit start/completion','command_attempts.csv':'Exact commands, PIDs, timestamps, actual exits and durable logs','target_diagnostics.csv':'Preserved zeros, repeated/negative targets and extrema','verification_summary.csv':'Per-unit exits, fit/metric/artifact counts and zero-fit resume','evidence_reuse_ledger.csv':'Original historical and current source/run/protocol identities; zero historical refits','completion_overlay.csv':'New18/195 overlay; original matrix preserved','remaining_queue_updated.csv':'177 pending units in unchanged order, updated timing scenarios','measured_timing_references.csv':'Actual same-dataset measurements used for estimates','analysis_validation.json':'Reconciled exact completion and verification counts'}
        text+='| File | Purpose |\n|---|---|\n'
        for file,purpose in purposes.items():text+=f'| [{file}](../../{final.relative_to(ROOT).as_posix()}/{file}) | {purpose} |\n'
        text+='\n## Reproducible figures\n\n'
        for name in ['forecast_error','coverage','interval_width','winkler','cost_and_error']:
            prefix='../../'+final.relative_to(ROOT).as_posix()+'/figures/'+name
            text+=f'- {name}: [PNG]({prefix}.png), [PDF]({prefix}.pdf), [source CSV/hash sidecar]({prefix}.sources.json).\n'
    if (REVIEW/'delivery_v1/delivery_validation.json').exists():
        text+='\n## Final delivery verification and next proposal\n\n[Delivery validation](delivery_v1/delivery_validation.json) reconciles all twelve successful model runs, 120 learned fits, 36 point cells, 72 interval cells, 72 exact saved-model checks, twelve zero-fit resumes and 26 distinct regression checks. [Selected configurations](delivery_v1/selected_configurations.csv) retain each model\'s parameters and original evidence identity. [Figure review](delivery_v1/figure_review.json) verifies the five rendered figures against their source hashes.\n\n'
        text+='[Coordinator recovery](RECOVERY_PROGRESS_WRITE.md), [outer command attempts](delivery_v1/coordinator_attempts.csv), and [calendar timing](delivery_v1/coordinator_timing.json) record the initial bookkeeping exit 1 and resumed exit 0. The independent preservation check is in the analysis directory. No learned fit was repeated.\n\n'
        text+='[Proposed seed-43 replication](delivery_v1/proposed_seed43_replication.csv) lists thirteen exact fold-2 keys, 104 tuning and 26 final fits. It is not authorized or launched. The remaining core queue contains 177 units; broader methods remain separate obligations.\n\n'
        if (REVIEW/'delivery_v1/publication_line_endings.json').exists():
            text+='[Publication byte-preservation correction](delivery_v1/publication_line_endings.json) records two preparation files whose initial Git blobs normalized line endings. Exact working bytes were re-staged under the existing binary-preservation attributes; scientific source, fitted artifacts and numerical values were unaffected. Publication now checks every staged blob against the working manifest before committing.\n\n'
    text+='\n## Per-unit fitted evidence\n\n'
    for u in manifest['units']:
        run=Path(u['run']).relative_to(ROOT).as_posix();design=Path(u['design']).relative_to(ROOT).as_posix();done=state.get('units',{}).get(u['stem'],{})
        text+='### '+ ' / '.join(map(str,u['key']))+'\n\n'
        text+=f'[Protocol](../../{design}/frozen_protocol.json), [memberships](../../{design}/membership.csv.gz), [readiness](../../{design}/readiness.json). '
        if done.get('validated'):
            text+=f'[Point metrics](../../{run}/point_summary.csv), [interval metrics](../../{run}/interval_quality.csv), [fit journal](../../{run}/fit_calls.jsonl), [fitted artifacts and all streams](../../{run}/units). '
            audit=Path(done['audit']).relative_to(ROOT).as_posix();resume=Path(done['resume']).relative_to(ROOT).as_posix()
            text+=f'[Independent validation](../../{audit}/validation.json), [saved-model checks](../../{audit}/saved_model_verification.csv), [zero-fit resume](../../{resume}).\n\n'
        else:text+='Pending; consult the live progress ledger.\n\n'
    text+='Each completed model directory retains its fitted object, normalization state, own calibration residuals, prediction rows, tuning predictions/history, payload and COMPLETE hashes. Persistence uses model.json; XGBoost uses model.ubj plus booster_config.json; LSTM uses model.pt. All scientific data remain unclipped.\n\n'
    text+='## Preservation and recomputation\n\n[Evidence manifest](EVIDENCE_MANIFEST.csv) hashes all current task artifacts except the manifest itself. The Git commit binds the manifest. The mutable coordinator lock and external publication/backup receipts remain outside OneDrive. Historical runs are linked with original source identities; newer source checks are not forced onto older runs. [Dataset notices](DATA_NOTICE.md) retain attribution.\n\n'
    text+='From the repository root, use the following with an unused output directory to recreate numeric tables and figures from saved artifacts; fitting routes are forbidden. The command also regenerates the report and current status documents, so use a separate review checkout for reproduction if preserving the delivered editorial text.\n\n```powershell\n& C:/cfs_venv/Scripts/python.exe -B review/matched_overnight_20260914/analyze.py final --out C:/Users/nigel/ConfoSenseBackups/matched_overnight_20260914/recomputed_analysis_v1\n```\n\nFor exact model reloads use each unit\'s recorded validate argv with a fresh receipt path and the preserved original source/data identity. Do not overwrite historical runs or receipts.\n'
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
    for name in ['MATCHED_OVERNIGHT_BATCH_REPORT.md','PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
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
        subprocess.run(['git','commit','-m',f'Publish matched overnight evidence: {label}'],cwd=ROOT,check=True)
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
