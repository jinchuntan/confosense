"""Publication cost plot with a central legend clear of the observed points."""
from common import *
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

out=REVIEW/'delivery_v1/cost_figure_v3';out.mkdir(exist_ok=False)
source=BATCH/'analysis_v1/fold2_five_seed_comparison.csv'
frame=pd.read_csv(source,float_precision='round_trip');assert len(frame)==195
colors={'persistence':'#555555','xgboost':'#0072B2','attention_lstm':'#D55E00'}
labels={'pleia':'PLEIA temperature','pleia_energy':'PLEIA energy','rico':'RICO temperature','bdg2':'BDG2 electricity'}
units={'pleia':'degrees C','rico':'degrees C','pleia_energy':'kWh per 10 minutes','bdg2':'kWh per hour'}
fig,axes=plt.subplots(2,2,figsize=(13,10),layout='constrained')
for ax,ds in zip(axes.ravel(),labels):
    f=frame[frame.dataset==ds];horizons=sorted(f.physical_minutes.unique());markers=dict(zip(horizons,['o','s','^','D']))
    for (model,minutes),p in f.groupby(['model','physical_minutes']):
        ax.scatter(p.model_phase_seconds,p.mae,color=colors[model],marker=markers[minutes],s=24,alpha=.3)
        ax.scatter([p.model_phase_seconds.mean()],[p.mae.mean()],color=colors[model],marker=markers[minutes],s=85,edgecolors='black',linewidths=.7)
    handles=[Line2D([],[],color=c,lw=3,label=m.replace('_',' ')) for m,c in colors.items()]
    handles += [Line2D([],[],color='black',marker=markers[h],linestyle='none',label=f'{h:g} min') for h in horizons]
    ax.legend(handles=handles,loc='upper center',ncol=2,fontsize=8)
    ax.set_xscale('log');ax.margins(x=.15,y=.25);ax.grid(alpha=.2)
    ax.set_title(labels[ds]);ax.set_xlabel('Measured model-phase wall seconds (log scale)');ax.set_ylabel('MAE ('+units[ds]+')')
fig.suptitle('All five training seeds: large outlined markers are means; small markers are individual runs')
exports=[]
for ext in ('png','pdf'):
    path=out/f'cost_and_error.{ext}';fig.savefig(path,dpi=160);exports.append(dict(path=path.name,sha256=sha(path)))
plt.close(fig)
atomic(out/'sources.json',dict(source_csv=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),script=Path(__file__).relative_to(ROOT).as_posix(),script_sha256=sha(__file__),files=exports,models_fitted=0,values_unchanged=True,revision='Original text labels overlapped; the second layout obscured extreme points with corner legends. Central legends and extra vertical margin preserve visible points. Earlier exports remain intact.'))
