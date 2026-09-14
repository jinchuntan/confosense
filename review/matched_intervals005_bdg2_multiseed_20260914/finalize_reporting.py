"""Seal the no-fit reporting artifacts after editorial report expansion."""
from common import *


def main():
    out=BATCH/'analysis_v1'
    report=(ROOT/'BDG2_MATCHED_INTERVAL_METHODS_MULTISEED_REPORT.md').read_text(encoding='utf-8')
    assert '584 to 3,737 per cell' in report
    assert '8,087.16 seconds (7,886.44 CPU seconds)' in report
    generator=REVIEW/'report.py'
    for metric in ('coverage','mpiw','winkler'):
        path=out/f'figures/five_seed_{metric}.sources.json'
        value=read(path);value['generator_sha256']=sha(generator);atomic(path,value)
        assert value['inputs']['common_support_metrics.csv']==sha(out/'common_support_metrics.csv')
        assert value['inputs']['five_seed_summary.csv']==sha(out/'five_seed_summary.csv')
    files=tree(out);files.pop('COMPLETE.json',None)
    atomic(out/'COMPLETE.json',dict(files=files,models_fitted=0,calibrators_fitted=0,report_finalized=True,utc=now()))
    assert read(out/'analysis_validation.json')['models_fitted']==0
    print('reporting artifacts finalized; zero fits')


if __name__=='__main__':main()
