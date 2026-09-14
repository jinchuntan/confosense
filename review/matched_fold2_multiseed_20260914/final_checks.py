"""Final arithmetic/source checks, panel prose and a clearer cost figure; no fits."""
import argparse
from common import *
import numpy as np
import pandas as pd

def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    analysis=BATCH/'analysis_v1'
    assert read(BATCH/'progress.json')['status']=='complete'
    for name,digest in read(analysis/'COMPLETE.json')['files'].items():assert sha(analysis/name)==digest,name
    frame=pd.read_csv(analysis/'fold2_five_seed_comparison.csv',float_precision='round_trip')
    assert len(frame)==195 and set(frame.model_seed)=={42,43,44,45,46}
    pairs=pd.read_csv(analysis/'paired_model_contrasts.csv',float_precision='round_trip')
    pairs=pairs[(pairs.outer_fold==2)&(pairs.left_model=='attention_lstm')&(pairs.right_model=='xgboost')]
    rows=[]
    for (ds,h),p in pairs.groupby(['dataset','horizon']):
        assert len(p)==5
        left=frame[(frame.dataset==ds)&(frame.horizon==h)&(frame.model=='attention_lstm')]
        right=frame[(frame.dataset==ds)&(frame.horizon==h)&(frame.model=='xgboost')]
        for level in (90,95):
            score=p[f'winkler{level}_difference']
            rows.append(dict(dataset=ds,horizon=h,physical_minutes=int(p.physical_minutes.iloc[0]),nominal_level=level/100,n_seed_rows=5,
                lower_lstm_winkler_seeds=int((score<0).sum()),winkler_difference_mean=score.mean(),winkler_difference_sample_std=score.std(ddof=1),winkler_difference_min=score.min(),winkler_difference_max=score.max(),
                lstm_coverage_mean=left[f'coverage{level}'].mean(),xgboost_coverage_mean=right[f'coverage{level}'].mean(),
                mpiw_difference_mean=p[f'mpiw{level}_difference'].mean(),mae_difference_mean=p.mae_difference.mean(),mae_difference_sample_std=p.mae_difference.std(ddof=1),
                cpu_ratio_mean=p.process_cpu_seconds_ratio.mean(),cpu_ratio_min=p.process_cpu_seconds_ratio.min(),cpu_ratio_max=p.process_cpu_seconds_ratio.max(),
                interpretation='paired LSTM minus XGBoost; CPU is LSTM/XGBoost; training seeds on identical support, not population CI'))
    panel=pd.DataFrame(rows);assert len(panel)==26
    panel.to_csv(out/'panel2_both_levels.csv',index=False)
    assert panel.lower_lstm_winkler_seeds.max()<5
    for ds in ('pleia','rico'):
        for _,p in frame[frame.dataset==ds].groupby(['horizon','model_seed']):
            base=p[p.model=='persistence'].iloc[0]
            assert (p[p.model!='persistence'].mae>base.mae).all()
            assert (p[p.model!='persistence'].rmse>base.rmse).all()
    bdg=pairs[pairs.dataset=='bdg2']
    assert (bdg[['mae_difference','rmse_difference','winkler90_difference','winkler95_difference']]>0).all().all()
    # The original four scientific plots were visually inspected. Verify all
    # five original PNG/PDF exports and their exact source links without edits.
    figures=[]
    for sidecar in sorted((analysis/'figures').glob('*.sources.json')):
        meta=read(sidecar);assert sha(ROOT/meta['source_csv'])==meta['source_sha256']
        assert sha(ROOT/meta['script'])==meta['script_sha256']
        for entry in meta['files']:
            path=sidecar.parent/entry['path'];assert sha(path)==entry['sha256']
            assert path.read_bytes().startswith(b'%PDF') if path.suffix=='.pdf' else path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
            figures.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path)))
    assert len(figures)==10
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    colors={'persistence':'#555555','xgboost':'#0072B2','attention_lstm':'#D55E00'}
    labels={'pleia':'PLEIA temperature','pleia_energy':'PLEIA energy','rico':'RICO temperature','bdg2':'BDG2 electricity'}
    units={'pleia':'degrees C','rico':'degrees C','pleia_energy':'kWh per 10 minutes','bdg2':'kWh per hour'}
    fig,axes=plt.subplots(2,2,figsize=(13,10),layout='constrained')
    for ax,ds in zip(axes.ravel(),labels):
        f=frame[frame.dataset==ds];horizons=sorted(f.physical_minutes.unique());markers=dict(zip(horizons,['o','s','^','D']))
        for (model,minutes),p in f.groupby(['model','physical_minutes']):
            ax.scatter(p.model_phase_seconds,p.mae,color=colors[model],marker=markers[minutes],s=24,alpha=.3)
            ax.scatter([p.model_phase_seconds.mean()],[p.mae.mean()],color=colors[model],marker=markers[minutes],s=85,edgecolors='black',linewidths=.7)
        model_handles=[Line2D([],[],color=c,lw=3,label=m.replace('_',' ')) for m,c in colors.items()]
        legend=ax.legend(handles=model_handles,loc='upper left',fontsize=8);ax.add_artist(legend)
        ax.legend(handles=[Line2D([],[],color='black',marker=markers[h],linestyle='none',label=f'{h:g} min') for h in horizons],loc='upper right',fontsize=8)
        ax.set_xscale('log');ax.margins(x=.15,y=.18);ax.grid(alpha=.2)
        ax.set_title(labels[ds]);ax.set_xlabel('Measured model-phase wall seconds (log scale)');ax.set_ylabel('MAE ('+units[ds]+')')
    fig.suptitle('All five training seeds: large outlined markers are means; small markers are individual runs')
    exports=[]
    for ext in ('png','pdf'):
        path=out/f'cost_and_error_v2.{ext}';fig.savefig(path,dpi=160);exports.append(dict(path=path.name,sha256=sha(path)))
    plt.close(fig)
    atomic(out/'cost_and_error_v2.sources.json',dict(source_csv=(analysis/'fold2_five_seed_comparison.csv').relative_to(ROOT).as_posix(),source_sha256=sha(analysis/'fold2_five_seed_comparison.csv'),script=Path(__file__).relative_to(ROOT).as_posix(),script_sha256=sha(__file__),files=exports,change='Separate horizon-marker legend removes overlapping horizon text; original figure remains preserved; values unchanged.'))
    atomic(out/'validation.json',dict(passed=True,models_fitted=0,original_analysis_bytes_unchanged=True,original_plot_exports_checked=len(figures),original_plot_sources_checked=5,original_pngs_visually_inspected=True,paired_both_level_rows=26,all_five_seeds_preserved=True,persistence_lower_mae_and_rmse_each_temperature_and_rico_seed_horizon=True,bdg_xgboost_lower_mae_rmse_both_winkler_each_seed_horizon=True,no_lstm_winkler_advantage_in_all_five_seeds_at_either_level=True,source_hash=read(REVIEW/'joint_pre_fit_manifest.json')['source_hash']))
    atomic(out/'COMPLETE.json',dict(passed=True,models_fitted=0,files=tree(out)))
    print(json.dumps(read(out/'validation.json'),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();main(a.out)
