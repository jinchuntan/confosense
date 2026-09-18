import copy,json
from common import *
def main():
 if git('branch','--show-current')!=BRANCH or git('rev-parse','main')!=MAIN:raise ValueError('branch preservation failure')
 m=read(REPO/'review/pleia_energy_context005_multiseed_20260915/pleia_energy_f2_s43_C_v1_execution_manifest.json');m['dataset']='pleia';m['model_seed']=42;m['expected_contexts']=68;m['expected_schedules']=2856
 if manifest().exists() and read(manifest())!=m:raise ValueError('manifest mismatch')
 atomic(manifest(),m)
 atomic(REVIEW/'USER_AUTHORIZATION.txt','User authorized exactly one PLEIA-temperature fold-2/h1 seed-42 C pilot, 2026-09-18.\n')
 atomic(REVIEW/'BATCH_SCOPE.json',dict(dataset='pleia',outer_fold=2,horizon=1,model_seed=42,contexts=68,schedules=2856,source_hash=SOURCE_HASH,execution_authorized=True))
 print(json.dumps(m,indent=2))
if __name__=='__main__':main()
