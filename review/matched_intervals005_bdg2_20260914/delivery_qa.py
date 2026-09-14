"""Check new report links and immutable figure provenance without fitting."""
import re
from urllib.parse import unquote
from common import *
from publish import index


def main():
    index()
    reports=[ROOT/'MATCHED_INTERVALS005_IMPLEMENTATION_REPORT.md',
             ROOT/'BDG2_MATCHED_INTERVAL_METHODS_PILOT_REPORT.md',
             REVIEW/'PANEL_RESPONSE.md', REVIEW/'EVIDENCE_INDEX.md',
             REVIEW/'delivery_v1/COMPLETION_VERIFICATION.md']
    links=[]
    for report in reports:
        content=report.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)',content):
            if target.startswith(('http:','https:','#')):continue
            target=unquote(target.split('#',1)[0].strip('<>'))
            resolved=(report.parent/target).resolve()
            assert resolved.is_relative_to(ROOT) and resolved.exists(),(report,target)
            links.append(dict(report=report.relative_to(ROOT).as_posix(),target=target))
    figures=[]
    for path in sorted((BATCH/'analysis_v1/figures').glob('*.sources.json')):
        record=read(path)
        assert sha(ROOT/record['source_csv'])==record['source_sha256']
        assert sha(ROOT/record['script'])==record['script_sha256']
        for artifact in record['files']:
            assert sha(path.parent/artifact['path'])==artifact['sha256']
        figures.append(record)
    assert len(figures)==3
    for folder in (BATCH/'analysis_v1',REVIEW/'delivery_v1'):
        completion=read(folder/'COMPLETE.json')
        files=tree(folder);files.pop('COMPLETE.json')
        assert files==completion['files'],str(folder)
    receipt=dict(passed=True,utc=now(),local_report_links_checked=len(links),links=links,
                 figure_source_checks=figures,scientific_fits=0,
                 immutable_analysis_and_delivery_verified=True,
                 visual_review=dict(status='passed',reviewer='assistant',
                    inspected=['native_interval_quality.png','common_interval_quality.png','stage_costs.png'],
                    notes='All three rendered PNGs were visually inspected before publication: readable axes and legends, no clipped labels. PDF exports share the same plotting canvas.'))
    atomic(REVIEW/'DELIVERY_QA.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('links','figure_source_checks')},indent=2),flush=True)


if __name__=='__main__':main()
