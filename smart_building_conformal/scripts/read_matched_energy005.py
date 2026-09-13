"""Read-only evaluated-source validation/resume for the preserved energy unit.

The fitted v1 files serialize Python None as an empty group field. Its original
metadata uniquely identifies that single source group. A declared CSV reader
maps only that representation to canonical 'None'; all checkpoint bytes and
numeric/row identities remain unchanged. No fitting command is exposed.
"""
import argparse,hashlib,json,sys,tempfile,zipfile
from pathlib import Path

SMART=Path(__file__).resolve().parents[1];REPO=SMART.parent
EVALUATED='7335d436f6e4f8c2144de372e8817d036bae216426c157f5bbdc1eb921927955'
ARCHIVE_HASH='8e353355ed6bf4b32ffc691463537eef3001f888b036a0a2b87650d06fd32e5a'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['validate','resume'])
 parser.add_argument('--receipt',required=True);args=parser.parse_args()
 archive=REPO/'review/matched_energy_h1_20260913/evaluated_source.zip'
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==ARCHIVE_HASH
 backup=Path('C:/Users/nigel/ConfoSenseBackups/matched_energy_h1_20260913/evaluated_readers')
 backup.mkdir(parents=True,exist_ok=True)
 extracted=Path(tempfile.mkdtemp(prefix='reader_',dir=backup))
 assert extracted.resolve().is_relative_to(backup.resolve())
 with zipfile.ZipFile(archive) as z:
  for name in z.namelist():
   prefix='smart_building_conformal/'
   assert name.startswith(prefix+'src/') and name.endswith('.py') and '..' not in Path(name).parts
   target=(extracted/name[len(prefix):]).resolve();assert target.is_relative_to(extracted.resolve())
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
 sys.path.insert(0,str(extracted))
 import pandas as pd
 from src import matched_forecasting005 as R
 from src.matched_models005 import forbid_fitting,PhaseMeter
 from src.unit_checkpoint import UnitCheckpoint,source_digest,digest
 assert source_digest()==EVALUATED
 # Data/config inputs stay in the original project; imported evaluated source
 # remains the byte-verified archive and is not relabelled as current source.
 R.ROOT=SMART;R.setup_threads()
 run=SMART/'outputs/matched_forecasting005/pleia_energy_h1_f0_s42_v1'
 protocol=SMART/'protocols/matched_forecasting005/pleia_energy_h1_f0_s42_v1/frozen_protocol.json'
 matrix=SMART/'outputs/amendment005/support_design_v1/experiment_matrix.csv'
 ready=protocol.with_name('readiness.json');key=('pleia_energy',1,0,42);receipt=Path(args.receipt)
 mappings=[]
 with forbid_fitting(),PhaseMeter() as total:
  if args.action=='resume':
   result=R.execute(protocol,matrix,key,run,ready,resume=True,forbid_fits=True)
  else:
   p=R.check_identity(protocol,matrix,key)
   data,roles=R.fresh_data(p)
   assert data['meta'].group_id.map(lambda x:x is None).all()
   all_ids=set(data['meta'].row_id)
   original_load=UnitCheckpoint.load
   def load_canonical(self,unit):
    loaded=original_load(self,unit)
    if loaded is None:return None
    payload,frames=loaded
    for name,frame in frames.items():
     if 'group_id' not in frame:continue
     assert set(frame.row_id)<=all_ids and frame.group_id.isin(['','None']).all()
     numeric_hash=hashlib.sha256(pd.util.hash_pandas_object(frame.drop(columns='group_id'),index=False).values.tobytes()).hexdigest()
     changed=int(frame.group_id.eq('').sum());frame['group_id']='None'
     assert numeric_hash==hashlib.sha256(pd.util.hash_pandas_object(frame.drop(columns='group_id'),index=False).values.tobytes()).hexdigest()
     destination=receipt/'canonical_streams'/unit/(name+'.csv.gz');destination.parent.mkdir(parents=True,exist_ok=True)
     frame.to_csv(destination,index=False,compression={'method':'gzip','mtime':0})
     mappings.append(dict(unit=unit,frame=name,rows=len(frame),empty_source_None_fields_canonicalized=changed,
       other_columns_hash=numeric_hash,other_columns_unchanged=True,original_checkpoint_unchanged=True))
    return payload,frames
   UnitCheckpoint.load=load_canonical
   from src.matched_validation005 import validate
   result=validate(run,protocol,matrix,key,receipt)
   pd.DataFrame(mappings).to_csv(receipt/'identifier_schema_mapping.csv',index=False)
 result.update(evaluated_source_hash=EVALUATED,reader_script_sha256=digest(Path(__file__)),
    evaluated_archive_sha256=ARCHIVE_HASH,reader_source_directory=str(extracted),
    identifier_schema='Python None serialized empty in v1; canonical string None verified against fresh original metadata',
    current_source_is_not_impersonated=True,compatibility_read_only=True,complete_reader_resources=total.result)
 target=receipt/'validation.json' if args.action=='validate' else receipt
 R.write_json(target,result,exclusive=args.action=='resume')
 print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
