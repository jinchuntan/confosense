"""Complete 130-cell native/common/miss-direction diagnostic, zero fitting."""
from common import *
import numpy as np,pandas as pd
from src.intervals005_common import Operations,csv
from src.context005_spec import table
BASE=SMART/'outputs/conditional_context005/implementation_support_v1'
OUT=SMART/'outputs/conditional_context005/interval_diagnostic_extension_v1'
with Operations(forbid=True):
    OUT.mkdir(parents=True,exist_ok=False);rows=[];hashes=[]
    for ds,run in [('pleia_energy','pleia_energy_f2_s42_v2'),('pleia','pleia_f2_s42_v1'),('rico','rico_f2_s42_v1'),('bdg2','bdg2_f2_s42_v1')]:
        stage=SMART/'outputs/matched_intervals005'/run/'stages';summary=table(stage/'tables/native_support_metrics.csv');common=table(stage/'tables/common_support_metrics.csv')
        for cell in summary.to_dict('records'):
            h=int(cell['horizon']);l=cell['level'];method=cell['method'];path=stage/f'stream_h{h}_l{int(l*100)}_{method}'/'issued.csv.gz';f=table(path);hashes.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
            if method=='dscp':
                cal=table(stage/'dscp_joint'/f'calibration_h{h}.csv.gz');calerror=cal.point-cal.y_true;score='frozen cluster/step signed y-minus-matched-XGBoost prediction; linear quantiles';pool='joint-origin calibration'
            else:
                kind='cqr' if method in ['quantile_uncalibrated','cqr'] else 'enbpi';suffix=f'h{h}_{kind}'+(f'_l{int(l*100)}' if kind=='cqr' else '')
                cal=table(stage/('raw_'+suffix)/f'calibration_{int(l*100)}.csv.gz');m=table(stage/('raw_'+suffix)/'calibration_metadata.csv.gz');calerror=cal.point-m.y_true
                score='asymmetric native tails' if method=='cqr' else 'none: uncalibrated raw quantiles' if method=='quantile_uncalibrated' else 'signed own-point online residual with finite sample ranks' if method.endswith('updated') else 'native MAPIE OOB calibration score'
                pool='historical calibration plus causal available released scores' if method.endswith('updated') else 'fixed historical calibration'
            c=common[(common.horizon==h)&(common.level==l)&(common.method==method)].iloc[0]
            rows.append(dict(dataset=ds,horizon=h,level=l,method=method,native_n=len(f),common_n=int(c.n),native_coverage=cell['coverage'],common_coverage=c.coverage,
                coverage_support_delta=cell['coverage']-c.coverage,available=int(f.available.sum()),unavailable=int((~f.available).sum()),below_fraction=float((f.observed<f.lower).mean()),above_fraction=float((f.observed>f.upper).mean()),
                cal_own_prediction_bias=float(calerror.mean()),test_own_prediction_bias=float((f.point-f.observed).mean()),cal_absolute_error_q95=float(np.quantile(abs(calerror),.95)),test_absolute_error_q95=float(np.quantile(abs(f.point-f.observed),.95)),
                mpiw=cell['mpiw'],winkler=cell['winkler'],score_convention=score,score_pool=pool,units='kWh per interval' if ds in ['pleia_energy','bdg2'] else 'degrees Celsius'))
    csv(OUT/'all_method_diagnostic.csv',pd.DataFrame(rows));csv(OUT/'input_hashes.csv',pd.DataFrame(hashes))
    atomic(OUT/'validation.json',dict(passed=len(rows)==130,native_common_cells=len(rows),source_unchanged=all(sha(ROOT/r['path'])==r['sha256'] for r in hashes),models_fitted=0,calibrators_fitted=0))
    print('ALL 130 SEED42 METHOD CELLS DIAGNOSED WITHOUT FITTING')
