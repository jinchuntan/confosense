"""No-fitting support arithmetic, versioned contexts and exact study inventory.

Uses the existing local prepared cache, bound to the published preflight hashes.
The exported observation/role tables also permit independent schedule verification.
"""
from __future__ import annotations
import argparse, contextlib, gc, hashlib, itertools, json, math, pickle, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src import split_integrity as SI
from src.operational004_design import STRATA, DESIGN, make_outer_folds, nested_roles, segments, physical_rules, seed_for
from src.operational004_events import corruption, _allocate
from src.unit_checkpoint import signature, source_digest
from src.pilot_data import build_support, pilot_roles, role_records

BASE=ROOT/'outputs/amendment004/preflight_20260913_v1'
ENTRY='9b5acb49531ce12706285c3f040310c0ab6053dd'
PROPOSAL=dict(version='amendment005_proposal_v1',status='post_inspection_proposal',models_fitted=0,
    incidence=.5,historical_min_recall=.6,historical_max_workload=1.,historical_catalogues=list(range(42,47)),
    challenge_replicates=[42,43],challenge_signs=[-1,1],context_seed=20260913,
    pleia_context_steps=144,rico_context='one whole run',
    warmup_minutes={'pleia':360,'pleia_energy':360,'rico':60},followup_minutes=60,
    min_distinct_effective_contexts_per_stratum=5,min_original_units=5,
    challenge_selection='none; fixed controlled evaluation only',
    catalogue_B_criterion='complete 21-rotation cycles; >=5 successes with probability >=.95 under random-missing mask only',
    precision_diagnostic='original-unit paired 2000-draw bootstrap, seed20240601, >=1900 supported draws; report unavailable otherwise',
    full_study_ready=False,publication_ready=False)

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()

@contextlib.contextmanager
def no_fitting():
    calls=[];old=sys.getprofile()
    def guard(frame,event,arg):
        if event=='call' and frame.f_code.co_name in {'fit','partial_fit','tune','run_unit','train','train_epoch','_fit_point'}:
            module=frame.f_globals.get('__name__','')
            if module.startswith(('src.','sklearn.','xgboost.','torch.','mapie.')):
                calls.append(module+'.'+frame.f_code.co_name)
                raise AssertionError('Fitting forbidden: '+calls[-1])
    sys.setprofile(guard)
    try:yield calls
    finally:sys.setprofile(old)

def request_count(days):return math.floor(.5*days+.5)
def allocation_counts(q,rotations):
    counts=np.zeros(21,int)
    for r in rotations:
        for e in range(q):counts[(e+r)%21]+=1
    return counts
def binomial_minimum(p,k=5,prob=.95):
    for n in range(k,10000):
        failure=sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k))
        if 1-failure>=prob:return n
    raise ValueError('criterion not reached')

def grouped_batch_folds(meta):
    groups=sorted(meta.group_id.unique(),key=lambda g:(meta.loc[meta.group_id.eq(g),'origin_time'].min(),str(g)))
    step=len(groups)//5;pos=np.arange(len(meta));out=[]
    for fold in range(3):
        a=step*(4-fold);b=len(groups) if fold==0 else a+step
        pool=pos[meta.group_id.isin(groups[:a])];test=pos[meta.group_id.isin(groups[a:b])]
        fit,cal=SI.refit_split(meta,pool,SI.GROUPED)
        SI.assert_boundary(meta,np.r_[fit,cal],test,SI.GROUPED)
        out.append(dict(train=fit,calibration=cal,test=test,scheme=SI.GROUPED))
    return out

def forecast_roles(meta,h,freq,fold,grouped):
    if not grouped:return pilot_roles(meta,h,freq,fold,3)
    f=grouped_batch_folds(meta)[fold];fit=f['train']
    blocks=SI.ordered_blocks(meta,fit,[1/3]*3,SI.GROUPED)
    roles=dict(fit=fit,calibration=f['calibration'],test=f['test'],inner0_train=blocks[0],
        inner0_validation=blocks[1],inner1_train=np.r_[blocks[0],blocks[1]],inner1_validation=blocks[2])
    for a,b in [('fit','calibration'),('calibration','test'),('inner0_train','inner0_validation'),('inner1_train','inner1_validation')]:
        SI.assert_boundary(meta,roles[a],roles[b],SI.GROUPED)
    return roles

def contexts(meta,ds,freq,fold,role):
    records=[];duration=max(4,math.ceil(60/(freq/pd.Timedelta('1min'))))
    warm=math.ceil(PROPOSAL['warmup_minutes'][ds]/(freq/pd.Timedelta('1min')))
    follow=math.ceil(60/(freq/pd.Timedelta('1min')))
    for group,sid,rows in segments(meta,freq):
        size=144 if ds.startswith('pleia') else len(rows)
        for start in range(0,len(rows)-size+1,size):
            rr=rows[start:start+size]
            if size<warm+duration+follow:continue
            cid=signature([ds,fold,role,group,str(meta.iloc[rr[0]].target_time)])[:20]
            rng=np.random.default_rng(seed_for('amendment005',PROPOSAL['context_seed'],cid))
            onset=int(rng.integers(warm,size-duration-follow+1))
            records.append(dict(context_id=cid,group_id=group,segment_id=sid,context_rows=rr,
                onset_offset=onset,duration=duration,warmup=warm,followup=follow))
    return records

def schedule(meta,y,ds,freq,fold,role,scales):
    cs=contexts(meta,ds,freq,fold,role);rows=[];ctx=[]
    for c in cs:
        rr=c['context_rows'];j=c['onset_offset'];pick=rr[j:j+c['duration']]
        sigma=float(scales.get(c['group_id'],scales['__pooled__']))
        ctx.append(dict(dataset=ds,outer_fold=fold,role=role,**{k:v for k,v in c.items() if k!='context_rows'},
            context_start_row_id=meta.iloc[rr[0]].row_id,context_end_row_id=meta.iloc[rr[-1]].row_id,
            onset_row_id=meta.iloc[pick[0]].row_id,onset=str(meta.iloc[pick[0]].target_time),
            context_rows=len(rr),sigma=sigma,context_row_hash=signature(meta.iloc[rr].row_id.tolist())))
        for family,severity in STRATA:
            for rep,sign in zip(PROPOSAL['challenge_replicates'],PROPOSAL['challenge_signs']):
                seed=seed_for('amendment005',c['context_id'],family,severity,rep)
                observed,available=corruption(y[pick],family,severity,sigma,sign,np.random.default_rng(seed),y[rr[j-1]])
                effective=bool((~available).any() or np.any(observed[available]!=y[pick][available]))
                rows.append(dict(dataset=ds,outer_fold=fold,role=role,context_id=c['context_id'],group_id=c['group_id'],
                    family=family,severity=severity,replicate=rep,sign=sign,mask_seed=str(seed),sigma=sigma,
                    onset=str(meta.iloc[pick[0]].target_time),onset_row_id=meta.iloc[pick[0]].row_id,
                    end_row_id=meta.iloc[pick[-1]].row_id,requested=True,hostable=True,placed=True,
                    effective=effective,null=not effective,rejected=False,
                    changed_values=int(np.sum(available & (np.nan_to_num(observed)!=y[pick]))),
                    unavailable_readings=int((~available).sum()),mask_hash=signature(available.tolist()),
                    observed_hash=signature(np.nan_to_num(observed,nan=-1.23456789e307).tolist())))
    return pd.DataFrame(ctx),pd.DataFrame(rows)

def generate(cache_dir,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'proposal_spec.json').write_text(json.dumps(PROPOSAL,indent=2)+'\n')
    summary=json.loads((BASE/'summary.json').read_text());pubroles=pd.read_csv(BASE/'memberships_summary.csv')
    pubbank=pd.read_csv(BASE/'event_support.csv');pubstrata=pd.read_csv(BASE/'stratum_support.csv')
    puballoc=pd.read_csv(BASE/'catalogue_summary.csv')
    inventory=[];role_rows=[];banks=[];strata=[];alternatives=[];context_rows=[];schedules=[];members=[];revised_roles=[]
    group_rows=[];forecast_members=[];fc_roles=[];fc_matrix=[];source_inputs=[];current_events=[];rules=[];source_files=[]
    tracked=subprocess.check_output(['git','ls-files','outputs','protocols','configs'],cwd=ROOT).decode().splitlines()
    for name in tracked:
        p=ROOT/name;source_files.append(dict(path=name,sha256=digest(p),bytes=p.stat().st_size))
    (out/'entry_preservation.json').write_text(json.dumps(dict(entry_commit=ENTRY,files=source_files),indent=2)+'\n')
    for ident in summary['datasets']:
        ds=ident['dataset'];cp=Path(cache_dir)/(ds+'_prepared.pkl')
        with cp.open('rb') as f:c=pickle.load(f)
        source_inputs.append(dict(path=str(cp),sha256=digest(cp),bytes=cp.stat().st_size))
        p,w,cfg=c['prepared'],c['w'],c['cfg'];meta=w['meta'];y=w['y'];freq=p.freq
        actual=signature(dict(meta=hashlib.sha256(pd.util.hash_pandas_object(meta,index=False).values.tobytes()).hexdigest(),
            features=hashlib.sha256(pd.util.hash_pandas_object(w['X'],index=False).values.tobytes()).hexdigest()))
        assert actual==w['data_hash']==ident['data_hash']
        assert np.array_equal(y,meta.y_true.to_numpy())
        raw=sum(s.n for s in p.series);days=len(meta)*freq/pd.Timedelta('1D');q=request_count(days)
        inventory.append(dict(dataset=ds,target=p.target_description,frequency_minutes=freq/pd.Timedelta('1min'),
            primary_horizon=ident['horizon'],original_rows=raw,eligible_rows=len(meta),groups=meta.group_id.nunique(),
            segments=len(segments(meta,freq)),asset_days=days,raw_asset_days=raw*freq/pd.Timedelta('1D'),
            all_eligible_requests=q,all_eligible_five_catalogue_bound=5*q,raw_five_catalogue_bound=5*request_count(raw*freq/pd.Timedelta('1D')),
            minimum_count_exposure_days=41,minimum_eligible_rows=math.ceil(41*pd.Timedelta('1D')/freq),
            data_hash=actual,outcomes_hash=hashlib.sha256(y.tobytes()).hexdigest()))
        for series in p.series:
            group_rows.append(dict(dataset=ds,group_id=str(series.group_id),raw_rows=series.n,
                start=str(series.frame.index.min()),end=str(series.frame.index.max()),season_steps=series.season_steps,
                phase=series.metadata.get('phase'),scheduler_step=series.metadata.get('step'),target_id=series.target_id))
        if ds!='bdg2':
            scheme=SI.GROUPED if ds=='rico' else 'chronological';oldfolds=make_outer_folds(meta,scheme,3,ident['horizon'],freq)
            newfolds=grouped_batch_folds(meta) if ds=='rico' else oldfolds
            obs=meta[['row_id','group_id','origin_time','target_time']].copy();obs['y']=y
            for fi,fold in enumerate(oldfolds):
                roles=nested_roles(meta,fold,scheme)
                for role,idx in roles.items():
                    sub=meta.iloc[idx].reset_index(drop=True);old=pubroles[(pubroles.dataset==ds)&(pubroles.outer_fold==fi)&(pubroles.role==role)].iloc[0]
                    assert SI.membership_hash(meta,idx)==old.membership_hash
                    duration=max(4,math.ceil(60/(freq/pd.Timedelta('1min'))));tol=10 if ds=='rico' else 6
                    guard=max(max(r['m'] for r in physical_rules(freq) if r['applicable']),tol)
                    segs=segments(sub,freq);exposure=len(sub)*freq/pd.Timedelta('1D')
                    starts=sum(max(0,len(rr)-duration-tol) for _,_,rr in segs)
                    slots=sum(1+(len(rr)-duration-tol-1)//(duration+guard) for _,_,rr in segs if len(rr)>=duration+tol+1)
                    role_rows.append(dict(**old.to_dict(),segments=len(segs),eligible_onset_positions=starts,guarded_capacity_per_catalogue=slots,
                        request_per_catalogue=request_count(exposure),frequency_minutes=freq/pd.Timedelta('1min'),horizon_steps=ident['horizon']))
                    if role not in ['inner0_selection','inner1_selection','outer_test']:continue
                    a=puballoc[(puballoc.dataset==ds)&(puballoc.outer_fold==fi)&(puballoc.role==role)]
                    s=pubstrata[(pubstrata.dataset==ds)&(pubstrata.outer_fold==fi)&(pubstrata.role==role)].copy()
                    bank=pubbank[(pubbank.dataset==ds)&(pubbank.outer_fold==fi)&(pubbank.role==role)].iloc[0]
                    requested=request_count(exposure);expected=allocation_counts(requested,range(5))
                    ordered=s.set_index(['family','severity']).loc[list(STRATA)]
                    assert np.array_equal(ordered.requested.to_numpy(),expected)
                    ev=pd.concat([pd.read_csv(BASE/f'{ds}_f{fi}_{role}_e{seed}_catalogue.csv.gz',keep_default_na=False) for seed in range(42,47)],ignore_index=True)
                    current_events.append(ev.assign(dataset=ds,outer_fold=fi,role=role))
                    eff=ev[ev.effective.astype(bool)] if len(ev) else ev
                    current=dict(**bank.to_dict(),asset_days=exposure,requested_per_catalogue=requested,
                        requested=int(a.requested.sum()),hostable_requested=int((ev.reason!='unhostable_group').sum()) if len(ev) else 0,
                        placed=int(a.placed.sum()),null=int(a.null.sum()),rejected=int(a.rejected.sum()),
                        original_groups=sub.group_id.nunique(),faulted_original_groups=eff.group_id.nunique(),
                        request_missing_strata=int((expected==0).sum()),request_min_per_stratum=int(expected.min()),
                        count_impossible=5*requested<105,allocation_impossible=expected.min()<5,
                        null_probability_random_missing_low=.9**duration)
                    banks.append(current);strata.append(s.assign(request_arithmetic=expected[[STRATA.index((f,v)) for f,v in zip(s.family,s.severity)]]))
                    min_n=binomial_minimum(1-.9**duration);K=None if requested==0 else 21*math.ceil(min_n/requested)
                    alternatives.append(dict(dataset=ds,outer_fold=fi,role=role,current_days=exposure,current_catalogues=5,
                        A_count_possible=5*requested>=105,A_supported=bool(bank.structural_event_support),
                        B_min_days_five_catalogues=41,B_extra_days_lower_bound=max(0,41-exposure),
                        B_required_221minute_runs=math.ceil(41*1440/221) if ds=='rico' else None,
                        B_mask_success_probability=1-.9**duration,B_min_requests_per_stratum=min_n,
                        B_fixed_catalogues_complete_cycles=K,B_guarantees_other_nulls_or_precision=False,
                        B_allocation_change_needed='catalogue-rotated remainder ties for run coverage' if ds=='rico' else 'complete 21-stratum rotation bank',
                        C_recommended=True,C_estimand='effective-fault conditional recall; separate null rate and clean workload'))
            for fi,fold in enumerate(newfolds):
                roles=nested_roles(meta,fold,scheme);rowrole=[[] for _ in range(len(meta))]
                for role,idx in roles.items():
                    for j in idx:rowrole[int(j)].append(role)
                    sub=meta.iloc[idx]
                    revised_roles.append(dict(dataset=ds,outer_fold=fi,role=role,n=len(idx),groups=sub.group_id.nunique(),
                        origin_min=str(sub.origin_time.min()),origin_max=str(sub.origin_time.max()),target_min=str(sub.target_time.min()),target_max=str(sub.target_time.max()),
                        asset_days=len(idx)*freq/pd.Timedelta('1D'),membership_hash=SI.membership_hash(meta,idx)))
                obs[f'fold{fi}_roles']=['|'.join(r) for r in rowrole]
                for role,train in [('inner0_selection','inner0_train'),('inner1_selection','inner1_train'),('outer_test','final_fit')]:
                    idx=roles[role];sub=meta.iloc[idx].reset_index(drop=True)
                    ctx,ev=schedule(sub,y[idx],ds,freq,fi,role,SI.training_scale(y,meta,roles[train]))
                    context_rows.append(ctx);schedules.append(ev)
                    for r in physical_rules(freq):
                        rules.append(dict(dataset=ds,outer_fold=fi,role=role,**r,complete_context_supported=r['applicable'] and r['m']<=PROPOSAL['warmup_minutes'][ds]/(freq/pd.Timedelta('1min')),
                            reason='frequency or complete warm-up/envelope/follow-up exceeds fixed context' if not r['applicable'] or r['m']>PROPOSAL['warmup_minutes'][ds]/(freq/pd.Timedelta('1min')) else 'supported'))
            obs.to_csv(out/f'{ds}_operational_membership_observations.csv.gz',index=False)
            if ds=='rico':
                p.metadata['run_audit'].to_csv(out/'rico_source_run_audit.csv',index=False)
        for h in cfg['horizons']:
            data=build_support(p,cfg,h,24);fm=data['meta'];fmembers=fm[['row_id','group_id','origin_time','target_time']].copy()
            seasonal=np.isfinite(fm.seasonal_naive_pred.to_numpy(float))
            for fi in range(3):
                roles=forecast_roles(fm,h,freq,fi,ds=='rico');rolehash=signature(role_records(fm,roles));labels=[[] for _ in range(len(fm))]
                for role,idx in roles.items():
                    for j in idx:labels[int(j)].append(role)
                    fc_roles.append(dict(dataset=ds,horizon=h,outer_fold=fi,role=role,n=len(idx),groups=fm.iloc[idx].group_id.nunique(dropna=False),
                        **{k:v for k,v in role_records(fm,{role:idx})[role].items() if k!='n'},
                        seasonal_rows=int(seasonal[idx].sum())))
                fmembers[f'fold{fi}_roles']=['|'.join(r) for r in labels]
                if ds=='pleia' and fi==0:
                    prior=json.loads((ROOT/'protocols/model_comparison_pilot_v1/frozen_protocol.json').read_text())['horizons'][str(h)]
                    assert data['data_hash']==prior['data_hash'] and role_records(fm,roles)==prior['roles']
                for seed,model,level in itertools.product(range(42,47),['persistence','xgboost','attention_lstm','seasonal_naive'],[.9,.95]):
                    reuse=ds=='pleia' and fi==0 and seed==42 and model!='seasonal_naive'
                    na=model=='seasonal_naive' and (ds=='rico' or not seasonal[np.r_[roles['calibration'],roles['test']]].all())
                    fc_matrix.append(dict(dataset=ds,horizon=h,horizon_minutes=h*freq/pd.Timedelta('1min'),outer_fold=fi,model_seed=seed,model=model,level=level,
                        status='inapplicable' if na else 'completed_reusable' if reuse else 'required_new',
                        reason='no within-run daily history' if na and ds=='rico' else 'incomplete seasonal common support' if na else 'exact pilot data and role hashes matched' if reuse else 'generic matched entrypoint required',
                        role_bank_hash=rolehash,data_hash=data['data_hash'],fit_n=len(roles['fit']),calibration_n=len(roles['calibration']),test_n=len(roles['test']),
                        original_test_groups=fm.iloc[roles['test']].group_id.nunique(dropna=False),tuning_fits=4 if model in ['xgboost','attention_lstm'] else 0,
                        final_fits=1 if model in ['xgboost','attention_lstm'] else 0,fit_count_scope='per unique dataset/horizon/fold/seed/model, shared across levels',
                        preserved_path=f'outputs/model_comparison_pilot_v1/runs/pilot_v1_20260913/units/h{h}_f0_s42_{model}' if reuse else '',
                        membership_version='amendment005_whole_run_batches' if ds=='rico' else 'matched_pilot_protocol'))
            fmembers.to_csv(out/f'{ds}_h{h}_forecast_membership.csv.gz',index=False)
            del data;gc.collect()
        del c,p,w,meta;gc.collect();print('NO-FIT AUDITED',ds,flush=True)
    events=pd.concat(schedules,ignore_index=True);challenge=[]
    for (ds,fi,role),ev in events.groupby(['dataset','outer_fold','role'],sort=False):
        for family,severity in STRATA:
            sub=ev[(ev.family==family)&(ev.severity==severity)];eff=sub[sub.effective]
            original=eff.group_id.nunique() if ds=='rico' else eff.context_id.nunique()
            challenge.append(dict(dataset=ds,outer_fold=fi,role=role,family=family,severity=severity,
                requested=len(sub),placed=len(sub),effective=len(eff),null=int(sub.null.sum()),
                distinct_effective_onsets=len(eff[['group_id','onset']].drop_duplicates()),effective_original_units=original,
                supported=original>=5 and len(eff[['group_id','onset']].drop_duplicates())>=5))
    for name,table in [('inventory',inventory),('current_roles',role_rows),('current_banks',banks),('current_strata',pd.concat(strata)),
        ('alternatives',alternatives),('original_groups',group_rows),('proposal_roles',revised_roles),('challenge_contexts',pd.concat(context_rows)),
        ('challenge_schedules',events),('challenge_support',challenge),('challenge_rule_applicability',rules),
        ('forecast_roles',fc_roles),('experiment_matrix',fc_matrix),('current_events',pd.concat(current_events))]:
        pd.DataFrame(table).to_csv(out/(name+('.csv.gz' if name in ['challenge_schedules','current_events'] else '.csv')),index=False)
    rank=pd.read_csv(BASE/'calibration_rank_support.csv',keep_default_na=False,na_values={'window':['']});rank=rank[rank.dataset.ne('bdg2')]
    rank.groupby(['dataset','outer_fold','role','method','level','strategy','window'],dropna=False).agg(
        groups=('group_id','nunique'),initial_n_min=('initial_calibration_n','min'),initial_rank_all=('initial_rank_supported','all'),
        online_n_min=('update_pool_n','min'),online_rank_all=('online_rank_supported','all')).reset_index().to_csv(out/'rank_support.csv',index=False)
    result=dict(passed=True,entry_commit=ENTRY,source_hash=source_digest(),script_hash=digest(__file__),models_fitted=0,
        proposal_spec_hash=digest(out/'proposal_spec.json'),input_caches=source_inputs,
        published_preflight_hash=digest(BASE/'summary.json'),historical_role_hashes_verified=len(role_rows),
        forecast_roles=len(fc_roles),forecast_level_cells=len(fc_matrix),challenge_variants=len(events),
        challenge_supported_strata=sum(r['supported'] for r in challenge),challenge_stratum_cells=len(challenge),
        preserved_files=len(source_files),full_study_ready=False,publication_ready=False)
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='input_caches'},indent=2))
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--cache-dir',required=True);a.add_argument('--out',required=True);args=a.parse_args()
    with no_fitting() as fits:generate(args.cache_dir,args.out)
    assert not fits
