"""Verify fetched publication bytes and representative exact GitHub downloads."""
from common import *
import csv,hashlib,json,re,urllib.request,urllib.parse

def main(output):
    subprocess.run(['git','fetch','origin',BRANCH],cwd=ROOT,check=True)
    head=git('rev-parse','HEAD');remote=git('rev-parse','FETCH_HEAD');assert head==remote,(head,remote)
    manifest=list(csv.DictReader((REVIEW/'EVIDENCE_MANIFEST.csv').open(encoding='utf-8')))
    # One git process validates every artifact from the fetched commit, including
    # working-byte line endings; no per-file network or subprocess fanout.
    queries=''.join(head+':'+r['path']+'\n' for r in manifest).encode()
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    data,_=process.communicate(queries);assert process.returncode==0
    offset=0
    for row in manifest:
        end=data.index(b'\n',offset);header=data[offset:end].split();assert header[1]==b'blob',header
        size=int(header[2]);payload=data[end+1:end+1+size]
        assert size==int(row['bytes']) and hashlib.sha256(payload).hexdigest()==row['sha256'],row['path']
        offset=end+size+2
    assert offset==len(data)
    links=[]
    for name in ['EVIDENCE_INDEX.md','IMPLEMENTATION_REPORT.md','SUPPORT_GATE_STATUS.md','INTERVAL_FAILURE_DIAGNOSTIC.md','FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md','PROTOCOL_TO_CODE_CROSSWALK.md']:
        path=REVIEW/name
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if re.match(r'https?://',target):continue
            resolved=(path.parent/urllib.parse.unquote(target.split('#')[0])).resolve()
            assert resolved.exists(),(name,target);links.append(dict(document=name,target=target))
    chosen=[REVIEW/'EVIDENCE_INDEX.md',REVIEW/'IMPLEMENTATION_REPORT.md',REVIEW/'FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md',REVIEW/'first_run_published_schedules.csv.gz',SMART/'src/context005_validate.py',SMART/'src/conditional_context005.py',SMART/'outputs/conditional_context005/implementation_support_v1/scope_crosswalk.csv',SMART/'outputs/conditional_context005/interval_diagnostic_extension_v1/all_method_diagnostic.csv',SMART/'outputs/conditional_context005/implementation_analysis_v1/interval_undercoverage.png',SMART/'outputs/conditional_context005/synthetic_pleia_energy_v1/stages/controls/controls.pkl',SMART/'outputs/conditional_context005/synthetic_rico_v1/stages/tables/events.csv.gz',SMART/'outputs/conditional_context005/synthetic_v1_coordinator/rico_resume.json']
    downloads=[]
    for path in chosen:
        relative=path.relative_to(ROOT).as_posix();url='https://raw.githubusercontent.com/jinchuntan/confosense/'+head+'/'+urllib.parse.quote(relative)
        with urllib.request.urlopen(url,timeout=45) as response:payload=response.read()
        actual=hashlib.sha256(payload).hexdigest();assert actual==sha(path),relative
        downloads.append(dict(path=relative,url=url,bytes=len(payload),sha256=actual))
    baseline=read(REVIEW/'PRESERVATION_BASELINE.json')
    for ref,value in baseline['prior_heads'].items():assert git('rev-parse',ref)==value
    result=dict(passed=True,published_commit=head,branch=BRANCH,all_manifest_artifacts_verified=len(manifest),local_document_links_verified=len(links),exact_downloads=downloads,main_unchanged=True,prior_heads_unchanged=True,utc=now())
    atomic(Path(output),result);print(json.dumps({k:v for k,v in result.items() if k!='exact_downloads'},indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);main(p.parse_args().output)
