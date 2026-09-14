"""Verify the new evidence commit and representative exact GitHub downloads."""
import argparse,csv,hashlib,json,re,subprocess,sys,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';REVIEW=Path(__file__).resolve().parent
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic,digest,now,read
BRANCH='review/pleia-energy-context005-pilot-20260915'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main(output):
    subprocess.run(['git','fetch','origin',BRANCH],cwd=ROOT,check=True)
    head=git('rev-parse','HEAD');assert git('rev-parse','FETCH_HEAD')==head
    manifest=list(csv.DictReader((REVIEW/'EVIDENCE_MANIFEST.csv').open(encoding='utf-8')))
    queries=''.join(head+':'+r['path']+'\n' for r in manifest).encode();proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    data,_=proc.communicate(queries);assert proc.returncode==0;offset=0
    for row in manifest:
        end=data.index(b'\n',offset);header=data[offset:end].split();assert header[1]==b'blob';size=int(header[2]);payload=data[end+1:end+1+size]
        assert size==int(row['bytes']) and hashlib.sha256(payload).hexdigest()==row['sha256'],row['path'];offset=end+size+2
    assert offset==len(data)
    links=[]
    for path in [REVIEW/'EVIDENCE_INDEX.md',REVIEW/'PLEIA_ENERGY_CONTEXT005_PILOT_REPORT.md',REVIEW/'NEXT_BOUNDED_PROPOSAL.md']:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if target.startswith('http'):continue
            resolved=(path.parent/urllib.parse.unquote(target.split('#')[0])).resolve();assert resolved.exists(),(path.name,target);links.append(target)
    chosen=[REVIEW/'EVIDENCE_INDEX.md',REVIEW/'PLEIA_ENERGY_CONTEXT005_PILOT_REPORT.md',REVIEW/'COMPLETION_VERIFICATION.json',
        SMART/'protocols/conditional_context005/pleia_energy_f2_s42_C_v1/frozen_protocol.json',
        SMART/'outputs/conditional_context005/first_real_C_v1_coordinator/validation/validation.json',
        SMART/'outputs/conditional_context005/first_real_C_v1_coordinator/resume.json',
        SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_analysis/control_rule_channel_summary.csv',
        SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_analysis/issued_consumed_hashes.csv.gz',
        SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_analysis/control_rule_comparison.png',
        SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_publication_v1/parts_manifest.csv',
        SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_publication_v1/contexts_01_08.zip']
    downloads=[]
    for path in chosen:
        relative=path.relative_to(ROOT).as_posix();url='https://raw.githubusercontent.com/jinchuntan/confosense/'+head+'/'+urllib.parse.quote(relative)
        with urllib.request.urlopen(url,timeout=120) as response:data=response.read()
        actual=hashlib.sha256(data).hexdigest();assert actual==digest(path),relative;downloads.append(dict(path=relative,bytes=len(data),sha256=actual,url=url))
    baseline=read(REVIEW/'PRESERVATION_BASELINE.json')
    for ref,value in baseline['prior_heads'].items():assert git('rev-parse',ref)==value
    result=dict(passed=True,commit=head,branch=BRANCH,manifest_files_verified=len(manifest),local_links_verified=len(links),
        representative_exact_downloads=downloads,main_unchanged=git('rev-parse','main')==baseline['main'],prior_heads_unchanged=True,utc=now())
    atomic(Path(output),result);print(json.dumps({k:v for k,v in result.items() if k!='representative_exact_downloads'},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);main(p.parse_args().output)
