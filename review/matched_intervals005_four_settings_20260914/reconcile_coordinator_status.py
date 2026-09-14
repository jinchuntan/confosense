"""Move the preserved pre-adoption launcher fault out of completed status."""
from common import *

def main():
    path=BATCH/'progress.json';state=read(path)
    if state['status']!='science_complete' or state.get('active') is not None:raise ValueError('scientific coordinator is not complete')
    if state.get('failure')!='name \'append\' is not defined':raise ValueError('unexpected status reconciliation input')
    state.setdefault('prior_failures',[]).append(dict(failure=state.pop('failure'),traceback=state.pop('traceback'),resolution='repaired missing journal import; adopted exact already-launched PLEIA-energy worker; no duplicate fit',reconciled_utc=now()))
    state['coordinator_reconciled']=True;state['updated_utc']=now();atomic(path,state);atomic(BACKUP/'latest_progress.json',state)
    print('coordinator status reconciled without changing scientific artifacts')

if __name__=='__main__':main()
