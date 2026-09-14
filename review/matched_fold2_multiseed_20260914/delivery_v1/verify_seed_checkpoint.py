import hashlib,json,subprocess,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
root=Path('C:/Users/nigel/OneDrive/Desktop/GitHub/confosense')
backup=Path(__file__).resolve().parent
seed=int(sys.argv[1]); assert seed in [43,44,45]
receipts=list(backup.glob(f'seed{seed}_*_publication.json'));assert len(receipts)==1
publication=json.loads(receipts[0].read_text());commit=publication['commit']
branch='review/matched-fold2-multiseed-20260914'
remote=subprocess.check_output(['git','-c','credential.helper=','ls-remote','origin','refs/heads/'+branch],cwd=root,text=True).strip()
assert remote==commit+'\trefs/heads/'+branch,remote
prefix=f'smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/seed{seed}_summary_v1/'
paths=['MATCHED_FOLD2_MULTISEED_REPORT.md','MATCHED_FAILURE_DIAGNOSIS.md','MATCHED_METHOD_READINESS_MAP.md',
       'review/matched_fold2_multiseed_20260914/EVIDENCE_INDEX.md']
paths += [prefix+p for p in ['analysis_validation.json','fold2_five_seed_comparison.csv','interval_quality.csv','run_costs.csv','verification_summary.csv','actual_seed_metadata.csv']]
checked=[]
for path in paths:
    req=urllib.request.Request(f'https://raw.githubusercontent.com/jinchuntan/confosense/{commit}/{path}',headers={'User-Agent':'ConfoSense-seed-checkpoint-verification'})
    with urllib.request.urlopen(req,timeout=45) as response:data=response.read()
    digest=hashlib.sha256(data).hexdigest()
    assert digest==hashlib.sha256((root/path).read_bytes()).hexdigest(),path
    checked.append(dict(path=path,bytes=len(data),sha256=digest))
result=dict(passed=True,utc=datetime.now(timezone.utc).isoformat(),seed=seed,branch=branch,commit=commit,remote_ref=remote,publication_method='GitHub Desktop signed-in session',raw_readbacks=len(checked),checks=checked)
out=backup/f'seed{seed}_remote_verification.json';assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
