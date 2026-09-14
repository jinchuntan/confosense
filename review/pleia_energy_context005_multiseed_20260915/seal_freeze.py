"""Record and commit the fully frozen batch before the first learned fit."""
from __future__ import annotations
import json,subprocess
from common import *

def main():
    if git('branch','--show-current')!=BRANCH:raise ValueError('wrong branch')
    pre=read(REVIEW/'PREFLIGHT_VALIDATION.json');assert pre['passed'] and pre['models_fitted']==0
    frozen=dict(version='pleia_energy_context005_multiseed_frozen_v1',source_hash=source_digest(),model_seeds=list(SEEDS),
        seed42_reused=True,manifests={str(s):digest(manifest(s)) for s in SEEDS},
        protocols={str(s):digest(design(s)/'frozen_protocol.json') for s in SEEDS},
        readiness={str(s):digest(design(s)/'readiness.json') for s in SEEDS},
        exact_commands=read(REVIEW/'BATCH_SCOPE.json')['commands'],preflight_sha256=digest(REVIEW/'PREFLIGHT_VALIDATION.json'),models_fitted=0,utc=now())
    atomic(REVIEW/'FROZEN_BATCH_MANIFEST.json',frozen)
    paths=[REVIEW,*(design(s) for s in SEEDS)]
    files=sorted({p for root in paths for p in (root.rglob('*') if root.is_dir() else [root]) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'})
    stage=BACKUP/'pre_fit_paths.txt';BACKUP.mkdir(parents=True,exist_ok=True);atomic(stage,'\n'.join(p.relative_to(REPO).as_posix() for p in files)+'\n')
    subprocess.run(['git','add','--pathspec-from-file='+str(stage)],cwd=REPO,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=REPO).returncode:
        subprocess.run(['git','commit','-m','Freeze authorized PLEIA-energy context005 multiseed batch'],cwd=REPO,check=True)
    frozen['evaluated_commit']=git('rev-parse','HEAD');atomic(REVIEW/'EVALUATED_COMMIT.json',frozen)
    subprocess.run(['git','add',str((REVIEW/'EVALUATED_COMMIT.json').relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m','Record multiseed evaluated commit'],cwd=REPO,check=True)
    print(json.dumps(dict(sealed=True,commit=git('rev-parse','HEAD'),source_hash=source_digest()),indent=2))

if __name__=='__main__':main()
