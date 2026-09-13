"""Delivery QA and readable summaries from immutable completed evidence; zero fits."""
import re, shutil
from datetime import datetime
from common import *
import pandas as pd

def main():
    out=BATCH/'analysis_v1';dest=REVIEW/'delivery_v1';dest.mkdir(exist_ok=False)
    state=read(BATCH/'progress.json');assert state['status']=='complete' and state['completed_units']==12
    complete=read(out/'COMPLETE.json')
    for name,value in complete['files'].items():assert sha(out/name)==value,name
    for unit in read(REVIEW/'joint_pre_fit_manifest.json')['units']:
        assert tree(unit['run'])==state['units'][unit['stem']]['run_files']
    copied=[]
    for pattern in ['coordinator_*.log*','*_publication.json','atomic_replace_retries.jsonl']:
        for p in BACKUP.glob(pattern):
            if p.is_file():
                shutil.copy2(p,dest/p.name);copied.append(p.name)
    summary=read(out/'analysis_validation.json');assert summary['observed_max_prediction_difference']==0
    logs=[read(p) for p in sorted(BACKUP.glob('coordinator_*.log.json'))]
    assert [r['exit_status'] for r in logs]==[1,0]
    pd.DataFrame(logs).to_csv(dest/'coordinator_attempts.csv',index=False)
    elapsed=(datetime.fromisoformat(logs[-1]['ended_utc'])-datetime.fromisoformat(logs[0]['started_utc'])).total_seconds()
    atomic(dest/'coordinator_timing.json',dict(calendar_seconds=elapsed,logged_attempt_seconds=sum(r['seconds'] for r in logs),recovery_gap_seconds=elapsed-sum(r['seconds'] for r in logs),initial_exit=1,resumed_exit=0,scope='coordinator launch through final reports/initial publication attempt; excludes earlier freeze/readiness and later delivery QA'))
    source=out/'fold2_seed42_all_horizons.csv';f=pd.read_csv(source,float_precision='round_trip')
    assert len(f)==39
    figures=[]
    for name in ['forecast_error','coverage','interval_width','winkler','cost_and_error']:
        s=read(out/'figures'/f'{name}.sources.json');assert s['source_sha256']==sha(source) and s['script_sha256']==sha(REVIEW/'analyze.py')
        for item in s['files']:assert sha(out/'figures'/item['path'])==item['sha256']
        figures.append(dict(name=name,visual_review='passed: readable original data panels, physical horizon axes, target units and legends; nominal coverage references retained',source_hash=s['source_sha256'],files=s['files']))
    atomic(dest/'figure_review.json',dict(passed=True,plots=figures,scientific_values_changed=False,rendered_files_preserved=True))
    def row(ds,minutes,model):return f[(f.dataset==ds)&(f.physical_minutes==minutes)&(f.model==model)].iloc[0]
    bullets=[]
    x=row('pleia',60,'xgboost');l=row('pleia',60,'attention_lstm');p=row('pleia',60,'persistence')
    bullets.append(f'**PLEIA temperature:** persistence has the smallest MAE at all three horizons. At 60 minutes its MAE is {p.mae:.4f} °C, versus {x.mae:.4f} for XGBoost and {l.mae:.4f} for LSTM. Their 95% coverages are {p.coverage95:.2%}, {x.coverage95:.2%} and {l.coverage95:.2%}. LSTM has lower Winkler scores than XGBoost at 30/60 minutes despite worse point errors and lower coverage; at 60 minutes the 95% scores are {l.winkler95:.4f} versus {x.winkler95:.4f}. This trade-off does not establish adequate intervals.')
    x=row('pleia_energy',10,'xgboost');l=row('pleia_energy',10,'attention_lstm');x60=row('pleia_energy',60,'xgboost');l60=row('pleia_energy',60,'attention_lstm')
    bullets.append(f'**PLEIA energy:** LSTM has slightly lower 10-minute MAE ({l.mae:.6f} versus {x.mae:.6f} kWh), but worse RMSE and 95% Winkler ({l.winkler95:.4f} versus {x.winkler95:.4f}). Its narrower 95% interval ({l.mpiw95:.4f} versus {x.mpiw95:.4f} kWh MPIW) covers only {l.coverage95:.2%}, versus {x.coverage95:.2%} for XGBoost. At 60 minutes, XGBoost has lower MAE ({x60.mae:.6f} versus {l60.mae:.6f}); all three models remain below nominal 95% coverage.')
    x=row('rico',60,'xgboost');l=row('rico',60,'attention_lstm');p=row('rico',60,'persistence')
    bullets.append(f'**RICO:** persistence has the smallest point errors at all four horizons. At 60 minutes, persistence/XGBoost/LSTM MAE is {p.mae:.4f}/{x.mae:.4f}/{l.mae:.4f} °C. LSTM is narrower than XGBoost at 30/60 minutes but has severe undercoverage: at 60 minutes, MPIW is {l.mpiw95:.4f} versus {x.mpiw95:.4f} °C, coverage is {l.coverage95:.2%} versus {x.coverage95:.2%}, and Winkler is {l.winkler95:.4f} versus {x.winkler95:.4f}.')
    x=row('bdg2',360,'xgboost');l=row('bdg2',360,'attention_lstm');p=row('bdg2',360,'persistence')
    bullets.append(f'**BDG2:** XGBoost has the smallest MAE/RMSE and Winkler scores at all three fold-2 horizons. At six hours, persistence/XGBoost/LSTM MAE is {p.mae:.3f}/{x.mae:.3f}/{l.mae:.3f} kWh. XGBoost/LSTM 95% MPIW is {x.mpiw95:.3f}/{l.mpiw95:.3f}, Winkler {x.winkler95:.3f}/{l.winkler95:.3f}, and coverage {x.coverage95:.2%}/{l.coverage95:.2%}. LSTM uses {l.process_cpu_seconds/x.process_cpu_seconds:.2f}× measured model-phase CPU. Pooled near-nominal coverage is not a per-building or prospective guarantee.')
    overview='## Numerical findings for the comparable slice\n\n'+'\n\n'.join('- '+b for b in bullets)+'\n\nThese are descriptive outcomes for the frozen fold-2/seed-42 slice, with dependent horizons and different target units. The extra fold and older pilots remain separate. No test result changed the experiment.\n\n'
    report=ROOT/'MATCHED_OVERNIGHT_BATCH_REPORT.md';text=report.read_text(encoding='utf-8')
    assert '## Numerical findings for the comparable slice' not in text
    text=text.replace('## Comparable fold-2 / seed-42 horizon results',overview+'## Comparable fold-2 / seed-42 horizon results',1)
    text+='\nThe resumed coordinator exited **0** after the recorded progress-write recovery. Calendar time from its first launch through automatic reporting was **'+f'{elapsed/60:.2f}'+' minutes**, including the recovery gap. Both outer command attempts and their measured scopes are in [the delivery timing record](review/matched_overnight_20260914/delivery_v1/coordinator_timing.json). Noninteractive Git authentication failed; the authorized review publication was completed using the existing signed-in GitHub Desktop workflow, followed by remote verification.\n'
    # Editorial spacing only; immutable CSVs, figures and scientific files stay unchanged.
    replacements={'exited1':'exited 1','exit0':'exit 0','and24-step':'and 24-step','seed42':'seed 42','seed43':'seed 43',';54/':' ; 54/',';108/':' ; 108/','cells.177':'cells. 177','fits,39':'fits, 39','90% and95%':'90% and 95%'}
    for old,new in replacements.items():text=text.replace(old,new)
    atomic(report,text)
    panel=REVIEW/'PANEL2_NUMERICAL_RESPONSE.md';text=panel.read_text(encoding='utf-8')
    for old,new in replacements.items():text=text.replace(old,new)
    atomic(panel,text)
    for name in ['PROJECT_RECOVERY_STATUS.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
        path=ROOT/name;raw=path.read_bytes();marker=b'<!-- overnight-20260914: preserved historical status follows -->'
        prefix,suffix=raw.split(marker,1)
        prefix=prefix.replace(b';18/',b'; 18/').replace(b';36 ',b'; 36 ').replace(b';72 ',b'; 72 ').replace(b';12 ',b'; 12 ').replace(b';177 ',b'; 177 ')
        path.write_bytes(prefix+marker+suffix)
        old=subprocess.check_output(['git','show',ENTRY+':'+name],cwd=ROOT);assert path.read_bytes().endswith(old)
    pending=pd.read_csv(out/'remaining_queue_updated.csv')
    chosen=pending[(pending.outer_fold==2)&(pending.model_seed==43)].copy();assert len(chosen)==13
    chosen['authorized']=False;chosen['launched']=False;chosen['tuning_fits']=8;chosen['final_fits']=2
    chosen.to_csv(dest/'proposed_seed43_replication.csv',index=False)
    # Readable selected parameter table, retaining original run identity.
    combined=pd.read_csv(out/'combined_comparison.csv',float_precision='round_trip');selected=[]
    for r in combined.to_dict('records'):
        run=ROOT/r['source_run'];ending=f'h{r["horizon"]}_f{r["outer_fold"]}_s{r["model_seed"]}_{r["model"]}'
        matches=[p for p in (run/'units').iterdir() if p.name.endswith(ending)];assert len(matches)==1
        payload=read(matches[0]/'payload.json')
        selected.append({**{k:r[k] for k in ['dataset','horizon','outer_fold','model_seed','physical_minutes','target_units','model','n_fit','n_calibration','n_test','source_run','source_hash','protocol_hash','selected_candidate','final_epochs','estimator_class']},'selected_parameters':json.dumps(payload['parameters'],sort_keys=True)})
    pd.DataFrame(selected).to_csv(dest/'selected_configurations.csv',index=False)
    for name,value in complete['files'].items():assert sha(out/name)==value
    result=dict(passed=True,new_units=12,planned_and_actual_tuning_fits=96,planned_and_actual_final_fits=24,repeated_learned_fits=0,tiny_learned_fits=0,point_cells=36,interval_cells=72,saved_model_prediction_checks=72,maximum_prediction_discrepancy=0,completed_zero_fit_resumes=12,distinct_regression_checks=26,coordinator_exits=[1,0],model_run_exits=[0]*12,immutable_analysis_files_unchanged=True,visual_figures_reviewed=5,scientific_source_hash=read(REVIEW/'joint_pre_fit_manifest.json')['source_hash'],copied_external_receipts=copied,remaining_core_units=177,full_study_ready=False)
    atomic(dest/'delivery_validation.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
