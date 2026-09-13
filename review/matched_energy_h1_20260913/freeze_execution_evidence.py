"""Archive exact evaluated sources and pre-fit evidence; no model execution."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(SMART))
from src.unit_checkpoint import digest,source_digest

def main():
 protocol=SMART/'protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/frozen_protocol.json'
 p=json.loads(protocol.read_text());ready=json.loads(protocol.with_name('readiness.json').read_text())
 assert p['source_hash']==source_digest()==ready['source_hash'] and ready['first_unit_ready']
 base=SMART/'outputs/matched_forecasting005'
 smoke=json.loads((base/'synthetic_smoke_v2/smoke_summary.json').read_text())
 assert smoke['passed'] and smoke['synthetic_learned_fits']==10
 assert json.loads((base/'synthetic_smoke_v2/protocol.json').read_text())['source_hash']==source_digest()
 assert json.loads((base/'preflight_v2/validation.json').read_text())['passed']
 sources={path:path.read_bytes() for path in sorted((SMART/'src').rglob('*.py'))}
 with zipfile.ZipFile(OUT/'evaluated_source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for path,raw in sources.items():archive.writestr(path.relative_to(ROOT).as_posix(),raw)
 # Reconstruct the first synthetic smoke's exact pre-freeze-helper source bytes;
 # accept the archive only if the complete source digest matches its saved identity.
 old=dict(sources);runner=SMART/'src/matched_forecasting005.py';text=old[runner].decode()
 text=text.replace("    if tuple(parent[k] for k in KEY_COLUMNS) == tuple(key):\n        for name in ['data_hash', 'role_bank_hash', 'fit_n', 'calibration_n', 'test_n']:\n            if chosen[name] != parent[name]:\n                raise ValueError('matrix/proposal mismatch: ' + name)",
 "    if tuple(parent[k] for k in KEY_COLUMNS) != tuple(key):\n        raise ValueError('this authorization requires the frozen first-unit proposal')\n    for name in ['data_hash', 'role_bank_hash', 'fit_n', 'calibration_n', 'test_n']:\n        if chosen[name] != parent[name]:\n            raise ValueError('matrix/proposal mismatch: ' + name)")
 text=text.replace('    config.update(dict(zip(KEY_COLUMNS, key)))\n','')
 text=text.replace("if data['data_hash'] != chosen['data_hash'] or signature(records) != chosen['role_bank_hash']:","if data['data_hash'] != parent['data_hash'] or signature(records) != parent['role_bank_hash']:")
 text=text.replace("if len(rows)!=len(expected) or set(data['meta'].iloc[rows].row_id) != set(expected.row_id):","if data['meta'].iloc[rows].row_id.tolist() != expected.row_id.tolist():")
 text=text.replace("version=f'matched_forecasting005_{key[0]}_h{key[1]}_f{key[2]}_s{key[3]}_execution_v1'","version='matched_forecasting005_energy_h1_execution_v1'")
 text=text.replace("    for filename, field in [('membership.csv.gz','membership_hash'),('boundaries.csv','boundaries_hash')]:\n        if field in protocol and digest(Path(protocol_path).parent/filename)!=protocol[field]:\n            raise ValueError('frozen support-file mismatch: '+filename)\n",'')
 old[runner]=text.encode()
 identity=hashlib.sha256('\n'.join(f"{path.relative_to(SMART/'src').as_posix()}:{hashlib.sha256(raw).hexdigest()}" for path,raw in old.items()).encode()).hexdigest()
 expected=json.loads((base/'synthetic_smoke_v1/protocol.json').read_text())['source_hash']
 assert identity==expected,(identity,expected)
 with zipfile.ZipFile(OUT/'synthetic_v1_source.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for path,raw in old.items():archive.writestr(path.relative_to(ROOT).as_posix(),raw)
 report=dict(status='ready_before_real_fitting',source_hash=source_digest(),protocol_hash=digest(protocol),
  source_archive_sha256=digest(OUT/'evaluated_source.zip'),synthetic_v1_source_hash=identity,
  synthetic_v1_archive_sha256=digest(OUT/'synthetic_v1_source.zip'),synthetic_v1_archive_method='reconstructed exact bytes; complete digest equals recorded executed source',
  current_regression_checks=8,synthetic_smoke_runs=2,total_synthetic_learned_fits=20,real_fits_so_far=0,
  planned_real_tuning_fits=8,planned_real_final_fits=2,published_role_banks_verified=39,
  pilot_historical_refits=0,first_unit_ready=True,full_study_ready=False,
  allowed_unit=['pleia_energy',1,0,42],source_commit='commit containing this pre-fit manifest; actual run records HEAD',
  launch_ram_note='Later user instruction makes 3 GiB launch reference nonblocking; readiness actually met it. Epoch/disk/numeric controls retained.')
 (OUT/'pre_fit_execution_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
